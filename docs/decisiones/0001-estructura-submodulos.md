# 0001 · Repositorio raíz con submódulos

- Fecha: 2026-10-31
- Estado: aceptada

## Contexto

Solaris tiene dos repositorios: el producto (`illariumcore`) y la landing (`solaris_fronted`). Se despliegan por separado, pero tienen que decir lo mismo: la landing no puede prometer lo que el producto no hace. Necesitamos un sitio para la documentación compartida (PRD, marca, decisiones) y una forma de saber qué versión de cada repositorio va con cuál.

## Opciones

1. **Submódulos git.** La raíz apunta a un commit concreto de cada repositorio.
2. **Clones ignorados más un script.** La raíz solo guarda `docs/`; los repositorios se clonan en carpetas ignoradas.
3. **Monorepo.** Fusionar los dos historiales en uno.

## Decisión

Submódulos: `product/` → `illariumcore` y `landing/` → `solaris_fronted`.

## Consecuencias

- Cada repositorio conserva su historial, su CI y su despliegue.
- Cada commit de la raíz registra un par alineado (producto, landing) junto con los documentos que lo justifican.
- Coste: hay que hacer push en dos pasos (primero el submódulo, luego el puntero en la raíz) y clonar con `--recurse-submodules`. Está explicado en el `README.md`.
- Descartamos el monorepo porque obligaría a reescribir historiales y a cambiar los despliegues sin necesidad.
