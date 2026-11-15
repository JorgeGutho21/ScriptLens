//! Contenedor de escritorio de ScriptLens IA.
//!
//! Responsabilidades:
//! 1. Arrancar el motor de análisis (backend Python) como proceso hijo.
//! 2. Leer su línea de arranque `{"event":"ready","port":..,"token":..}`.
//! 3. Entregar puerto y token a la interfaz mediante el comando `backend_info`.
//! 4. Finalizar el motor al cerrar la aplicación.
//!
//! El token solo vive en memoria; nunca se escribe en disco ni en registros.

use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};

use serde::{Deserialize, Serialize};
use tauri::{Manager, RunEvent};

#[derive(Clone, Serialize, Deserialize)]
struct BackendInfo {
    port: u16,
    token: String,
}

#[derive(Default)]
struct BackendState {
    info: Mutex<Option<BackendInfo>>,
    child: Mutex<Option<Child>>,
}

#[derive(Deserialize)]
struct ReadyLine {
    event: String,
    port: u16,
    token: String,
}

#[tauri::command]
fn backend_info(state: tauri::State<'_, Arc<BackendState>>) -> Option<BackendInfo> {
    state.info.lock().ok().and_then(|g| g.clone())
}

/// Construye el comando que inicia el motor de análisis.
/// - Producción: motor empaquetado con PyInstaller en los recursos de la aplicación.
/// - Desarrollo: intérprete del entorno virtual del repositorio.
fn backend_command(app: &tauri::AppHandle) -> Command {
    let bundled = app
        .path()
        .resource_dir()
        .map(|d| d.join("backend").join("scriptlens-backend.exe"))
        .unwrap_or_default();
    let mut cmd = if bundled.exists() {
        Command::new(bundled)
    } else {
        let repo = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
        let python = repo.join(".venv").join("Scripts").join("python.exe");
        let mut c = Command::new(python);
        c.arg("-m").arg("backend").current_dir(repo);
        c
    };
    // El motor vigila este PID y se cierra solo si la aplicación desaparece.
    cmd.env("SCRIPTLENS_PARENT_PID", std::process::id().to_string());
    if let Ok(dir) = app.path().app_local_data_dir() {
        cmd.env("SCRIPTLENS_DATA_DIR", dir);
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }
    cmd.stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::inherit());
    cmd
}

fn start_backend(app: &tauri::AppHandle, state: Arc<BackendState>) {
    let mut child = match backend_command(app).spawn() {
        Ok(c) => c,
        Err(e) => {
            eprintln!("No se pudo iniciar el motor de análisis: {e}");
            return;
        }
    };
    let stdout = child.stdout.take();
    *state.child.lock().unwrap() = Some(child);

    if let Some(out) = stdout {
        std::thread::spawn(move || {
            for line in BufReader::new(out).lines().map_while(Result::ok) {
                if let Ok(ready) = serde_json::from_str::<ReadyLine>(&line) {
                    if ready.event == "ready" {
                        *state.info.lock().unwrap() = Some(BackendInfo { port: ready.port, token: ready.token });
                    }
                }
            }
        });
    }
}

fn stop_backend(state: &BackendState) {
    if let Some(mut child) = state.child.lock().unwrap().take() {
        let _ = child.kill();
        let _ = child.wait();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let state = Arc::new(BackendState::default());
    let app = tauri::Builder::default()
        // Una sola instancia: abrir ScriptLens de nuevo enfoca la ventana existente
        // en lugar de iniciar un segundo motor de análisis.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.unminimize();
                let _ = w.show();
                let _ = w.set_focus();
            }
        }))
        .manage(state.clone())
        .invoke_handler(tauri::generate_handler![backend_info])
        .setup({
            let state = state.clone();
            move |app| {
                start_backend(app.handle(), state);
                Ok(())
            }
        })
        .build(tauri::generate_context!())
        .expect("error al construir ScriptLens IA");

    app.run(move |_handle, event| {
        if let RunEvent::Exit = event {
            stop_backend(&state);
        }
    });
}
