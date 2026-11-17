# Brief · Reel comercial «Alta de cliente»

- **Fecha y quién lo pide:** 2026-11-09, Diego.
- **Input original:** `raw/research/2026-11-09_encargo-reel-comercial.md`
- **Para quién y dónde se verá:** dueños de consultoras e implantadores de CRM ([[ADR-0011]]), en reels de TikTok e Instagram y en LinkedIn.
- **Qué debe quedar claro al terminar:** un implantador convierte las reglas de su cliente en un proceso con contrato, sin programar, y una persona sigue decidiendo.
- **Función del producto que enseña:** Contrato (editor y vista previa) y Revisar. Es la Fase 3 de `docs/plan-evolutivo.md`, ya en `main` de `illariumcore`.
- **Proceso y datos:** «Alta de cliente», el proceso de la línea base de H03 (`raw/eval-runs/2026-11-08_h03-linea-base.md`). La definición y los casos copian el fixture de `product/tests/process-cases.test.ts`. `src/datos-alta.ts` los valida y evalúa con las funciones del producto, y el render falla si el resultado cambia.
- **Formatos:** 9:16 (1080 × 1920) como pieza principal y 16:9.
- **Duración:** unos 34 s.

## Qué se aplica del input y qué no

| Del input | Decisión | Por qué |
|---|---|---|
| «Otra propuesta comercial» | Ángulo nuevo: el implantador crea el proceso de su cliente | La serie anterior enseñaba funciones; este reel enseña la oferta para el canal |
| «16:9 para reels» | 9:16 principal y 16:9 aparte | Los reels son verticales |
| Proceso cercano al CRM | «Alta de cliente», creado desde la app | Ya existe y está medido como línea base |
| Afirmar rapidez («en minutos») | Fuera | H03 no está medida con una persona |
| Ocultar que los casos no tienen documento | No: se ve «Sin fuente» y «casos de prueba escritos a mano» | Principio 1 |

## Guion

| Plano | Leyendas | En pantalla |
|---|---|---|
| Gancho | Implantas el CRM. / Las reglas del cliente siguen *en un PDF.* | Tipografía a pantalla completa |
| Regla | Escribe la regla en un formulario. *Sin programar.* / Así la lee *el motor.* | La frase de la regla y sus palabras volando al formulario; la lógica que da `describeLogic` |
| Contrato | Pruébala con casos *antes de publicar.* / Publicas una versión. *Queda registrada.* | Reglas, casos, vista previa y «Publicar versión» con el `policy_hash` real |
| Decide | Si la regla pide Riesgos, *Comercial no aprueba.* / Riesgos decide. *Queda en el registro.* | Rol bloqueado, cambio de rol, aprobación y fila de registro |
| Cierre | Tú aportas el proceso. Illarium aporta *el contrato.* | Logo, audiencia y «Pide una demo» |

## Mascota (2026-11-11)

Diego pide introducir a Solaris, la mascota, como logo y compañero en el 9:16. Fuente: `mascota/Isotipo principal-html/Main.dc.html` (carpeta local de Diego, sin versionar) y una imagen de referencia dorada.

- **Compañero:** `Companero` en `src/Reel.tsx`, por encima de las escenas. Entra en el gancho, se gira hacia la interfaz en una esquina, late cuando cada palabra llega al formulario, se inclina ante un hueco, niega cuando el rol no puede aprobar y salta al publicar y al aprobar.
- **Logo:** en el cierre vuelve al centro con la palabra «Solaris» debajo.
- **No pulsa nada.** Mira y reacciona; quien decide en pantalla sigue siendo una persona (principio 3).
- **Una variante:** `ReelAlta-9x16` con la mascota dorada. Diego la eligió el 14/11 ([[ADR-0024]]); la variante de esfera negra se retiró.
- **Sin cambiar:** el 16:9 y `docs/marca.md`, que aún describe el sol de dos círculos.
