// Evita una consola adicional en Windows en compilaciones de producción.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    scriptlens_lib::run()
}
