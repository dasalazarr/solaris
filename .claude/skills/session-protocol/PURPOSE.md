# PURPOSE — session-protocol

Adapta los pasos 1–8 de WikiSkill (arXiv 2608.27454) al trabajo por sesiones: cada sesión es una **iteración** con una propuesta atómica, un gate de validación y un registro que persiste aunque se rechace.

Patrones y decisiones que la motivan:
- [[ADR-0001]]: WikiSkill como modelo del repositorio.
- [[R06]]: un fundador en solitario con un plazo fijo necesita que cada sesión retome el trabajo sin fricción.
- [[PAT-001]]: alcance acotado a una sola cuña.
