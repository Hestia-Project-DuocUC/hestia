# Cómo contribuir a Hestia

## Ramas
- `main` → producción, protegida
- `develop` → integración, protegida
- `feat/nombre` → nuevas funcionalidades
- `fix/nombre` → corrección de bugs

## Commits
Usamos Conventional Commits:
- feat: nueva funcionalidad
- fix: corrección de bug
- docs: documentación
- refactor: reorganización
- chore: mantenimiento

## Flujo de trabajo
1. Partir siempre desde develop actualizado
2. Crear rama con nombre descriptivo
3. Hacer commits atómicos con mensajes claros
4. Abrir Pull Request hacia develop
5. Esperar revisión y aprobación
6. No hacer merge sin aprobación

## Reglas importantes
- Nunca subir archivos .env
- Nunca hacer push directo a main o develop
- Siempre correr el servidor localmente antes de subir
- Un PR por funcionalidad, no acumular cambios no relacionados