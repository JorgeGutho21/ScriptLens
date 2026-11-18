// ScriptLens IA — interacción ligera de la página. Sin dependencias.
// Sin JavaScript la página sigue funcionando: los módulos se muestran todos y las capturas se abren como enlaces.
(() => {
  'use strict'
  document.documentElement.classList.add('js')

  // Menú móvil
  const barra = document.getElementById('barra')
  const botonMenu = document.getElementById('boton-menu')
  const menu = document.getElementById('menu')
  const cerrarMenu = () => { menu.classList.remove('abierto'); botonMenu.setAttribute('aria-expanded', 'false') }
  botonMenu.addEventListener('click', () => {
    const abrir = !menu.classList.contains('abierto')
    menu.classList.toggle('abierto', abrir)
    botonMenu.setAttribute('aria-expanded', String(abrir))
  })
  menu.addEventListener('click', (e) => { if (e.target.closest('a')) cerrarMenu() })
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && menu.classList.contains('abierto')) { cerrarMenu(); botonMenu.focus() } })
  const borde = () => barra.classList.toggle('con-borde', window.scrollY > 8)
  window.addEventListener('scroll', borde, { passive: true })
  borde()

  // Sección actual en el menú
  const enlaces = [...menu.querySelectorAll('a[href^="#"]')]
  if ('IntersectionObserver' in window) {
    const obs = new IntersectionObserver((entradas) => {
      for (const en of entradas) {
        if (!en.isIntersecting) continue
        for (const a of enlaces) {
          if (a.getAttribute('href') === `#${en.target.id}`) a.setAttribute('aria-current', 'true')
          else a.removeAttribute('aria-current')
        }
      }
    }, { rootMargin: '-45% 0px -50% 0px' })
    enlaces.forEach((a) => { const s = document.querySelector(a.getAttribute('href')); if (s) obs.observe(s) })
  }

  // Explorador de módulos (patrón de pestañas accesible)
  const explorador = document.querySelector('[data-explorador]')
  if (explorador) {
    const tabs = [...explorador.querySelectorAll('[role="tab"]')]
    const vertical = () => window.matchMedia('(min-width: 961px)').matches
    const elegir = (tab, foco, desplazar = true) => {
      for (const t of tabs) {
        const sel = t === tab
        t.setAttribute('aria-selected', String(sel))
        t.tabIndex = sel ? 0 : -1
        document.getElementById(t.getAttribute('aria-controls')).hidden = !sel
      }
      if (foco) tab.focus()
      if (desplazar && !vertical()) tab.scrollIntoView({ block: 'nearest', inline: 'nearest' })
    }
    elegir(tabs[0], false, false)
    tabs.forEach((t, i) => {
      t.addEventListener('click', () => elegir(t, false))
      t.addEventListener('keydown', (e) => {
        const sig = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key]
        if (sig) { e.preventDefault(); elegir(tabs[(i + sig + tabs.length) % tabs.length], true) }
        if (e.key === 'Home') { e.preventDefault(); elegir(tabs[0], true) }
        if (e.key === 'End') { e.preventDefault(); elegir(tabs[tabs.length - 1], true) }
      })
    })
  }

  // Filtros de la galería
  const filtros = [...document.querySelectorAll('[data-filtro]')]
  const items = [...document.querySelectorAll('#galeria li')]
  filtros.forEach((b) => b.addEventListener('click', () => {
    filtros.forEach((x) => x.setAttribute('aria-pressed', String(x === b)))
    const f = b.dataset.filtro
    items.forEach((li) => { li.hidden = f !== 'todas' && li.dataset.cat !== f })
  }))

  // Visor de capturas
  const visor = document.getElementById('visor')
  if (!visor || typeof visor.showModal !== 'function') return
  const img = document.getElementById('visor-img')
  const texto = document.getElementById('visor-texto')
  let grupo = []
  let actual = 0
  const mostrar = (i) => {
    actual = (i + grupo.length) % grupo.length
    const a = grupo[actual]
    img.src = a.getAttribute('href')
    img.alt = a.querySelector('img')?.alt || ''
    texto.textContent = a.dataset.galeria
  }
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[data-galeria]')
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey) return
    e.preventDefault()
    const enGaleria = a.closest('#galeria')
    grupo = enGaleria
      ? [...document.querySelectorAll('#galeria li:not([hidden]) a[data-galeria]')]
      : [...document.querySelectorAll('a[data-galeria]:not(#galeria a)')]
    mostrar(grupo.indexOf(a))
    visor.showModal()
  })
  visor.addEventListener('click', (e) => {
    const mover = e.target.closest('[data-mover]')
    if (mover) return mostrar(actual + Number(mover.dataset.mover))
    if (e.target.closest('[data-cerrar]') || e.target === visor) visor.close()
  })
  visor.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') mostrar(actual + 1)
    if (e.key === 'ArrowLeft') mostrar(actual - 1)
  })
  visor.addEventListener('close', () => { img.removeAttribute('src') })
})()
