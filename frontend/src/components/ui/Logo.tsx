// Componente Logo — usa /public/logo.png (PNG con fondo blanco).
// prop `light=true`: envuelve en contenedor blanco redondeado para fondos oscuros
// (sidebar, login). De esta forma el fondo blanco del PNG se integra visualmente
// en lugar de contrastar con el fondo oscuro.
// No usamos CSS filter (brightness/invert) porque con PNG de fondo blanco
// el filtro invierte TODO incluyendo el fondo, generando un recuadro negro.

interface LogoProps {
  className?: string
  light?: boolean
}

export function Logo({ className = 'w-8 h-8', light = false }: LogoProps) {
  const img = (
    <img
      src="/logo.png"
      alt="Hestia"
      className={className}
      draggable={false}
    />
  )

  if (light) {
    return (
      <div className="bg-white rounded-xl p-0.5 inline-flex items-center justify-center flex-shrink-0">
        {img}
      </div>
    )
  }

  return img
}
