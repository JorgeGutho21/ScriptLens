[[TOC]]

# 1. Antes de empezar

Esta guía explica cómo instalar ScriptLens IA en un computador con Windows, paso a paso, aunque nunca haya usado GitHub. Cada captura se tomó del programa y del instalador reales.

Tabla: Qué necesita

| Requisito | Detalle |
|---|---|
| Sistema operativo | Windows 10 (versión 1809 o posterior) o Windows 11, de **64 bits** |
| Memoria RAM | 4 GB para el programa; 8 GB o más si quiere usar el asistente con IA |
| Espacio libre | 200 MB; unos 3 GB adicionales si instala el modelo de IA |
| Permisos | Su cuenta normal de Windows. No necesita ser administrador |
| Conexión a Internet | Solo para descargar. Después ScriptLens funciona sin conexión |

ScriptLens **no** funciona en Windows de 32 bits, Windows 7 u 8, macOS ni Linux. No necesita instalar Python, Node.js, Rust ni Visual Studio: el instalador ya trae todo lo necesario.

## 1.1 Cómo saber si su Windows es de 64 bits

1. Pulse la tecla **Windows**, escriba **Acerca de** y abra **Acerca de su PC**.
2. En **Tipo de sistema** debe decir «Sistema operativo de 64 bits, procesador basado en x64».

# 2. Método A: instalación gráfica (recomendada)

## 2.1 Abrir la página oficial

1. Abra su navegador: Google Chrome, Microsoft Edge o Firefox.
2. En la barra de direcciones (la parte superior, donde se escriben las páginas) escriba `github.com/JorgeGutho21/ScriptLens` y pulse **Enter**.
3. Compruebe que arriba a la izquierda aparece **JorgeGutho21 / ScriptLens**. Si el nombre es distinto, cierre la página: no es la oficial.

Figura: docs/instalacion/capturas/01_repositorio.png | Página oficial del repositorio en GitHub | Arriba a la izquierda se lee JorgeGutho21 / ScriptLens. En la columna derecha, el apartado Releases muestra «ScriptLens IA v0.1.0» con la etiqueta Latest.


## 2.2 Encontrar la versión publicada

1. En la columna derecha de la página, busque el apartado **Releases** y pulse sobre él (o sobre la versión que aparece debajo, marcada **Latest**).
2. Se abre la página de versiones. Use la más reciente que tenga la etiqueta verde **Latest**: es la versión estable.
3. Baje hasta el apartado **Assets** (archivos). Si está cerrado, pulse la palabra **Assets** para desplegarlo.

Figura: docs/instalacion/capturas/02_releases.png | Página de la versión v0.1.0 | La etiqueta verde Latest indica la versión estable. Más abajo están las notas de la versión y el apartado Assets.


## 2.3 Descargar el instalador correcto

En **Assets** verá varios archivos. Descargue estos dos:

Tabla: Archivos que debe descargar

| Archivo | Qué es |
|---|---|
| `ScriptLens-IA_0.1.0_x64-setup.exe` | El instalador para Windows de 64 bits |
| `ScriptLens-IA_0.1.0_x64-setup.exe.sha256` | La huella digital del instalador, para comprobar que no fue alterado |

Los archivos «Source code (zip)» y «Source code (tar.gz)» son el código fuente para programadores: **no** los necesita.

Figura: docs/instalacion/capturas/03_assets.png | Apartado Assets de la versión v0.1.0 | Los dos primeros archivos son los que debe descargar. Junto a cada uno, GitHub muestra el comienzo de su huella SHA-256 (sha256:111397cf…).

Pulse el nombre de cada archivo. El navegador lo guarda en la carpeta **Descargas**. Si el navegador pregunta si desea conservar el archivo, elija **Conservar**.

## 2.4 Comprobar la procedencia y la integridad

Antes de abrir un programa descargado conviene comprobar dos cosas:

1. **Procedencia:** que lo descargó de `github.com/JorgeGutho21/ScriptLens/releases` y no de otra página.
2. **Integridad:** que el archivo es exactamente el publicado. Para eso se compara su huella SHA-256.

Para comprobar la huella:

1. Abra la carpeta **Descargas**.
2. Haga clic derecho en un espacio vacío de la carpeta y elija **Abrir en Terminal** (en Windows 10: mantenga **Mayús** pulsada, clic derecho y **Abrir la ventana de PowerShell aquí**).
3. Copie y pegue este comando y pulse **Enter**:

```
Get-FileHash .\ScriptLens-IA_0.1.0_x64-setup.exe -Algorithm SHA256
```

4. Abra el archivo `.sha256` con el Bloc de notas (clic derecho → **Abrir con** → **Bloc de notas**).
5. Compare las dos huellas: las 64 letras y números deben ser iguales (mayúsculas o minúsculas da igual).

Si no coinciden, **no abra el instalador**: bórrelo y descárguelo de nuevo desde la página oficial.

## 2.5 Abrir el instalador

Haga doble clic en `ScriptLens-IA_0.1.0_x64-setup.exe`.

Como el instalador no tiene una firma de código comercial (un certificado de pago), Windows SmartScreen puede mostrar el aviso «Windows protegió su PC». Ese aviso es una protección útil y no debe ignorarse de forma automática. Continúe **solo si** se cumplen las dos condiciones del apartado 2.4: lo descargó de la página oficial y la huella coincide. En ese caso pulse **Más información** y después **Ejecutar de todas formas**. Si tiene cualquier duda, no continúe y consulte a alguien de confianza.

## 2.6 Seguir el asistente de instalación

El instalador tiene la identidad de ScriptLens IA y está en español. Sus pantallas aparecen en el orden siguiente; todas las capturas se tomaron del instalador real de la versión 0.1.0 en Windows 11 a escala 125 %.

**Paso 1. Bienvenida.** Recomienda cerrar las demás aplicaciones. Pulse **Siguiente**.

Figura: docs/instalacion/capturas/10_instalador_bienvenida.png | Pantalla de bienvenida del instalador | A la izquierda, la identidad del programa y del autor; a la derecha, las instrucciones. El botón Siguiente avanza.

**Paso 2. Acuerdo de licencia.** Muestra la licencia MIT de ScriptLens IA. Léala y pulse **Acepto**.

Figura: docs/instalacion/capturas/11_instalador_licencia.png | Pantalla del acuerdo de licencia | El texto completo de la licencia MIT se puede desplazar. Al pie se lee el aviso de derechos de autor.

**Paso 3. Ya está instalado** (solo aparece si ScriptLens IA ya estaba en el equipo). Con la misma versión ofrece «Añadir o reinstalar componentes» o «Desinstalar ScriptLens IA»; con una versión anterior ofrece desinstalarla antes o instalar encima. Deje la opción marcada y pulse **Siguiente**. Su historial y sus informes se conservan.

Figura: docs/instalacion/capturas/12_instalador_ya_instalado.png | Pantalla de mantenimiento cuando el programa ya está instalado | La primera opción, marcada por defecto, reinstala el programa sin borrar los datos.

**Paso 4. Elegir lugar de instalación.** Propone `C:\Users\<su usuario>\AppData\Local\ScriptLens IA` y muestra el espacio requerido (unos 162 MB). No hace falta cambiarla: es una carpeta de su usuario y por eso Windows no pide permisos de administrador. Pulse **Siguiente**; la instalación empieza de inmediato.

Figura: docs/instalacion/capturas/13_instalador_carpeta.png | Pantalla de elección de la carpeta de instalación | En la captura, la parte «Usuario» de la ruta es el nombre de la cuenta del equipo de pruebas; en su equipo aparecerá el suyo.

**Paso 5. Instalando.** Copia los archivos (entre 10 y 20 segundos). Si su Windows no tiene Microsoft Edge WebView2, el instalador lo descarga e instala en este paso; para eso necesita conexión a Internet. Cuando la barra se completa aparece «Instalación Completada»; pulse **Siguiente**.

Figura: docs/instalacion/capturas/14_instalador_instalando.png | Pantalla de progreso durante la copia de archivos | La línea superior indica el archivo que se está copiando. «Ver detalles» muestra la lista completa.

Figura: docs/instalacion/capturas/15_instalador_completado.png | Pantalla de instalación completada | La barra llena y la palabra Completado indican que la copia terminó sin errores.

**Paso 6. Finalización.** Dos casillas marcadas por defecto: «Ejecutar ScriptLens IA» y «Crear acceso directo en el escritorio». Desmarque la que no desee y pulse **Terminar**.

Figura: docs/instalacion/capturas/16_instalador_finalizar.png | Pantalla final del asistente | Si deja marcada la primera casilla, ScriptLens IA se abre al pulsar Terminar.

El instalador no instala servicios, no cambia la configuración de seguridad de Windows y no se ejecuta en segundo plano después de terminar.

## 2.7 Localizar y abrir ScriptLens

1. Pulse la tecla **Windows** y escriba **ScriptLens**.
2. Pulse **ScriptLens IA**. También puede usar el acceso directo del escritorio.

La primera vez puede tardar hasta 30 segundos en abrir, porque el antivirus revisa los archivos nuevos. Mientras tanto verá el mensaje «Iniciando el motor de análisis».

## 2.8 Configuración inicial

La primera vez aparece una guía de bienvenida. Léala con calma: explica qué analiza el programa, qué datos se quedan en su equipo y qué acciones piden confirmación. Al final puede elegir:

- **Modo sencillo:** muestra lo esencial con explicaciones. Recomendado si no tiene conocimientos técnicos.
- **Modo avanzado:** añade columnas técnicas como el PID o la firma digital.

Figura: docs/capturas/01_bienvenida.png | Guía de bienvenida | Puede volver a verla desde Ajustes.

## 2.9 Primer diagnóstico

1. Quédese un minuto en el **Panel general**. ScriptLens necesita ese tiempo para distinguir un consumo constante de un pico pasajero. Mientras tanto muestra «Recopilando mediciones».
2. Lea el recuadro de la derecha: resume si el equipo funciona con normalidad y por qué.
3. Abra **Seguridad** y pulse **Revisar ahora**. En unos segundos verá el estado del antivirus, del firewall y de los programas que se inician con Windows.

Figura: docs/capturas/02_panel_general.png | Panel general tras el primer minuto | Los anillos muestran el uso del procesador y de la memoria; el recuadro explica la situación.

## 2.10 Cómo entender los resultados

Tabla: Significado de los estados

| Estado | Qué significa | Qué hacer |
|---|---|---|
| Normal (verde) | Todo funciona dentro de lo esperado | Nada |
| Requiere revisión (amarillo) | Algo es poco habitual, pero **no** significa que sea peligroso | Leer la explicación y decidir con calma |
| Consumo elevado | Un programa usa mucho procesador o memoria de forma continua | Cerrarlo si no lo está usando |
| Amenaza detectada (rojo) | Solo aparece si Microsoft Defender detectó una amenaza | Seguir las indicaciones de Seguridad de Windows |

ScriptLens no es un antivirus: explica lo que mide y nunca califica un programa como malicioso por sí mismo.

# 3. Método B: instalación con PowerShell

Para usuarios que prefieren escribir comandos. Abra **PowerShell** desde el menú Inicio (no hace falta «Ejecutar como administrador»). Copie cada bloque, péguelo con clic derecho y pulse **Enter**. Las líneas que empiezan con `#` son comentarios: no hacen nada.

```
# 1. Ir a la carpeta Descargas y descargar los dos archivos de la versión v0.1.0
cd $HOME\Downloads
$base = "https://github.com/JorgeGutho21/ScriptLens/releases/download/v0.1.0"
$f = "ScriptLens-IA_0.1.0_x64-setup.exe"
Invoke-WebRequest "$base/$f" -OutFile $f
Invoke-WebRequest "$base/$f.sha256" -OutFile "$f.sha256"
```

Resultado esperado: no aparece ningún mensaje; los dos archivos quedan en Descargas.

```
# 2. Comparar la huella
$f = "ScriptLens-IA_0.1.0_x64-setup.exe"
$esperado = (Get-Content "$f.sha256").Split(" ")[0]
$real = (Get-FileHash $f -Algorithm SHA256).Hash
if ($real -eq $esperado) { "Coincide" } else { "NO coincide: no instale" }
```

Resultado esperado: la palabra `Coincide`.

```
# 3. Abrir el instalador gráfico
Start-Process ".\ScriptLens-IA_0.1.0_x64-setup.exe"
```

Si prefiere instalar sin ventanas, use `Start-Process ".\ScriptLens-IA_0.1.0_x64-setup.exe" -ArgumentList "/S" -Wait`. La instalación tarda entre 10 y 20 segundos y crea el acceso directo en el menú Inicio.

Esta guía nunca le pedirá ejecutar un script descargado directamente de Internet (por ejemplo, comandos con `iex` o `Invoke-Expression`). Si encuentra instrucciones así en otra página, no las use.

# 4. Método C: CMD y código fuente (desarrolladores)

Este método es para programadores que quieren modificar o compilar ScriptLens. **No es necesario para usar el programa.**

## 4.1 Descargar con el Símbolo del sistema

En **Símbolo del sistema** (menú Inicio → escriba `cmd`):

```
cd %USERPROFILE%\Downloads
set BASE=https://github.com/JorgeGutho21/ScriptLens/releases/download/v0.1.0
set F=ScriptLens-IA_0.1.0_x64-setup.exe
curl -L -O %BASE%/%F%
curl -L -O %BASE%/%F%.sha256
certutil -hashfile %F% SHA256
type %F%.sha256
```

Compare la huella que muestra `certutil` con la del archivo `.sha256`. Si coinciden: `start ScriptLens-IA_0.1.0_x64-setup.exe`.

## 4.2 Compilar desde el código fuente

Herramientas necesarias (solo para desarrollo): Git, Python 3.12, Node.js 20 o posterior, Rust estable y Visual Studio Build Tools con la carga «Desarrollo de escritorio con C++».

En **PowerShell**:

```
git clone https://github.com/JorgeGutho21/ScriptLens.git
cd ScriptLens
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -r backend\requirements-dev.txt pyinstaller
npm install
npm --prefix frontend install
.\.venv\Scripts\python -m pytest
npm run dev
```

`pytest` ejecuta las pruebas automáticas del motor; `npm run dev` abre la aplicación en modo de desarrollo. Para generar el instalador y su huella: `.\scripts\construir_instalador.ps1` (el resultado queda en `src-tauri\target\release\bundle\nsis\`). Si Rust indica `link.exe not found`, ejecute antes `. .\scripts\msvc-env.ps1` en la misma ventana.

# 5. Asistente de IA (opcional)

Todas las funciones, salvo la redacción con IA, funcionan sin instalar nada más.

1. Descargue Ollama desde su sitio oficial, `ollama.com/download`, instálelo y ábrelo.
2. En ScriptLens, abra **Asistente IA**. Si el indicador dice «Ollama no está instalado o no está abierto», pulse **Comprobar de nuevo**.
3. Pulse **Descargar** junto a «Qwen3 4B Instruct» y confirme. La descarga es de unos 2,5 GB y solo se hace una vez.
4. Cuando el indicador diga «Ollama activo», escriba una pregunta, por ejemplo «¿Por qué está lento el computador?».

Figura: docs/capturas/12_asistente_ia.png | Asistente con IA local | Cada respuesta indica si sus cifras se comprobaron con los datos medidos.

# 6. Problemas frecuentes

Tabla: Problemas y soluciones

| Problema | Solución |
|---|---|
| No encuentro **Releases** | Está en la columna derecha de la página del repositorio. En pantallas pequeñas aparece más abajo |
| «Windows protegió su PC» | Compruebe procedencia y huella (apartado 2.4). Si todo coincide, **Más información → Ejecutar de todas formas** |
| La huella no coincide | No instale. Borre el archivo y descárguelo de nuevo desde la página oficial |
| El programa se queda en «Iniciando el motor de análisis» | Espere un minuto la primera vez. Si sigue igual, cierre y vuelva a abrir; si persiste, reinstale |
| Ventana en blanco | Instale o repare «Microsoft Edge WebView2 Runtime» desde la página oficial de Microsoft |
| El asistente responde «sin IA» | Ollama no está abierto o el modelo no está descargado (apartado 5) |

# 7. Actualizar y desinstalar

**Actualizar:** en **Acerca de**, pulse **Buscar actualizaciones**. Si hay una versión nueva, descárguela como en el apartado 2, compruebe su huella e instálela encima de la anterior: su historial se conserva.

**Desinstalar:** abra **Configuración → Aplicaciones → Aplicaciones instaladas**, busque **ScriptLens IA**, pulse los tres puntos y elija **Desinstalar**. El historial se conserva por si vuelve a instalar, salvo que marque en el desinstalador la casilla «Eliminar los datos de aplicación»; también puede borrarlo antes desde **Ajustes → Privacidad**. Los informes de la carpeta Documentos no se borran. Ollama se desinstala aparte.

Para aprender a usar cada sección después de instalar, consulte el *Manual de usuario de ScriptLens IA*.
