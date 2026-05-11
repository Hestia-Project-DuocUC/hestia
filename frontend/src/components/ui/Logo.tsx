// Componente Logo — usa /public/logo.svg con soporte de color via CSS filter.
// prop `light=true` invierte el logo a blanco para fondos oscuros (sidebar, login).

interface LogoProps {
  className?: string
  light?: boolean
}

export function Logo({ className = 'w-8 h-8', light = false }: LogoProps) {
  return (
    <img
      src="/logo.svg"
      alt="Hestia"
      className={className}
      style={light ? { filter: 'brightness(0) invert(1)' } : undefined}
      draggable={false}
    />
  )
}
