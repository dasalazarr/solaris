# Solaris · espacio de trabajo

Repositorio raíz de Solaris, el producto de Illarium. Aquí viven la fuente de verdad compartida (`docs/`) y los dos repositorios del proyecto como submódulos. Cada uno conserva su historial y se despliega por separado; este repositorio registra qué versión de cada uno va alineada con la otra.

| Carpeta    | Qué es                                  | Repositorio                     |
|------------|-----------------------------------------|---------------------------------|
| `docs/`    | PRD, marca, decisiones y diario         | este                            |
| `product/` | La app (Next.js)                        | `dasalazarr/illariumcore`       |
| `landing/` | La landing comercial (Next.js estático) | `dasalazarr/solaris_fronted`    |

## Empezar

```bash
git clone --recurse-submodules https://github.com/dasalazarr/solaris.git
```

Si ya lo habías clonado sin submódulos:

```bash
git submodule update --init
```

Comandos de cada app:

- `product/`: `npm install`, `npm run dev`, `npm run lint`, `npm test`, `npm run build`. Variables en `product/.env.example`; códigos de espacio con `node scripts/nuevo-codigo.mjs`.
- `landing/`: `pnpm install`, `pnpm dev`, `pnpm lint`, `pnpm build`

## Flujo de trabajo

1. Una rama por tarea, con el mismo nombre en la raíz y en cada submódulo que toques.
2. Haz commit y push **dentro** del submódulo (`cd product && git push -u origin <rama>`).
3. Vuelve a la raíz y haz commit del puntero del submódulo junto con los cambios en `docs/`. Así queda registrado qué versión del producto corresponde a qué versión de la landing.
4. Nada va a `main` ni se despliega sin la confirmación de Diego.

## Reglas compartidas

- Identidad visual: [`docs/marca.md`](docs/marca.md). Los tokens se copian literalmente en ambos repositorios.
- Decisiones: [`docs/decisiones/`](docs/decisiones/).
- Instrucciones para el agente cofundador: [`CLAUDE.md`](CLAUDE.md).
