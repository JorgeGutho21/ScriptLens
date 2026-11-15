/** Glosario contextual en lenguaje sencillo. */
export const GLOSSARY: Record<string, { term: string; text: string }> = {
  cpu: {
    term: 'CPU (procesador)',
    text: 'Es la parte del computador que ejecuta las instrucciones de los programas. Si está ocupada casi al 100 % durante mucho tiempo, todo puede ir más lento.',
  },
  ram: {
    term: 'Memoria RAM',
    text: 'La memoria RAM almacena temporalmente los datos que utilizan los programas abiertos. Si está muy ocupada, el computador puede responder más lentamente.',
  },
  nucleo: {
    term: 'Núcleo',
    text: 'El procesador se divide en varios núcleos que trabajan a la vez. Un programa puede ocupar mucho un solo núcleo aunque el total parezca bajo.',
  },
  proceso: {
    term: 'Proceso',
    text: 'Cada programa en ejecución es uno o varios procesos. Windows también tiene procesos propios que funcionan sin ventana visible.',
  },
  disco: {
    term: 'Actividad de disco',
    text: 'Cantidad de datos que se leen o escriben por segundo en las unidades de almacenamiento. Una actividad alta y continua puede hacer más lento el equipo.',
  },
  red: {
    term: 'Actividad de red',
    text: 'Datos enviados y recibidos por segundo a través de las conexiones de red (Wi-Fi o cable).',
  },
  uptime: {
    term: 'Tiempo encendido',
    text: 'Tiempo transcurrido desde el último reinicio. Windows con inicio rápido puede conservar este valor al apagar; reiniciar lo pone en cero.',
  },
  sostenido: {
    term: 'Consumo sostenido',
    text: 'Promedio durante un periodo (por ejemplo, un minuto). Es más útil que un pico momentáneo para saber si algo realmente afecta al equipo.',
  },
  swap: {
    term: 'Archivo de paginación',
    text: 'Espacio del disco que Windows usa como memoria adicional cuando la RAM se llena. Es mucho más lento que la RAM.',
  },
}
