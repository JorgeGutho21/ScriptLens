import { useEffect, useRef } from 'react'

/**
 * Elemento 3D discreto: la «lente» de ScriptLens girando lentamente.
 * - Three.js se carga de forma diferida (no aumenta el tamaño inicial de la aplicación).
 * - Resolución limitada y renderizado solo cuando la ventana es visible.
 * - Con «Reducir animaciones» se dibuja un único fotograma estático.
 * - Si WebGL no está disponible, no se muestra nada (el resto de la interfaz no depende de él).
 */
export function Lens3D({ size = 160 }: { size?: number }) {
  const host = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let disposed = false
    let cleanup = () => {}
    import('three').then((THREE) => {
      if (disposed || !host.current) return
      let renderer: InstanceType<typeof THREE.WebGLRenderer>
      try {
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
      } catch {
        return
      }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
      renderer.setSize(size, size)
      host.current.appendChild(renderer.domElement)

      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 50)
      camera.position.set(0, 0, 7)
      const accent = new THREE.Color('#3b8cff')

      const group = new THREE.Group()
      const ring = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.2, 32, 96), new THREE.MeshStandardMaterial({ color: accent, metalness: 0.55, roughness: 0.25 }))
      const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.2, 1.3, 24), new THREE.MeshStandardMaterial({ color: accent, metalness: 0.5, roughness: 0.3 }))
      handle.position.set(1.33, -1.33, 0)
      handle.rotation.z = Math.PI / 4
      const glass = new THREE.Mesh(new THREE.CircleGeometry(1.08, 64), new THREE.MeshPhysicalMaterial({ color: '#9cc5ff', transparent: true, opacity: 0.16, roughness: 0.05, metalness: 0, side: THREE.DoubleSide }))
      group.add(ring, handle, glass)
      group.position.set(-0.35, 0.35, 0)
      scene.add(group)
      scene.add(new THREE.AmbientLight('#ffffff', 0.7))
      const key = new THREE.DirectionalLight('#ffffff', 1.6)
      key.position.set(3, 4, 5)
      scene.add(key)
      const rim = new THREE.PointLight('#6db0ff', 6, 12)
      rim.position.set(-3, -2, 3)
      scene.add(rim)

      const reduced = document.documentElement.dataset.motion === 'reduced' || window.matchMedia('(prefers-reduced-motion: reduce)').matches
      const clock = new THREE.Clock()
      let raf = 0
      const draw = () => {
        const t = clock.getElapsedTime()
        group.rotation.y = Math.sin(t * 0.6) * 0.6
        group.rotation.x = Math.sin(t * 0.4) * 0.15
        renderer.render(scene, camera)
      }
      const loop = () => {
        if (document.visibilityState === 'visible') draw()
        raf = requestAnimationFrame(loop)
      }
      if (reduced) {
        group.rotation.y = 0.35
        renderer.render(scene, camera)
      } else loop()

      cleanup = () => {
        cancelAnimationFrame(raf)
        scene.traverse((o) => {
          const m = o as InstanceType<typeof THREE.Mesh>
          m.geometry?.dispose?.()
          ;(m.material as { dispose?: () => void } | undefined)?.dispose?.()
        })
        renderer.dispose()
        renderer.domElement.remove()
      }
    })
    return () => {
      disposed = true
      cleanup()
    }
  }, [size])

  return <div ref={host} style={{ width: size, height: size }} aria-hidden="true" />
}
