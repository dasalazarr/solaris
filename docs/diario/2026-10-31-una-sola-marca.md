# Una sola marca antes del primer cliente

*Borrador. Pendiente de revisión.*

Teníamos dos Solaris. La landing tenía un sol dorado, una tipografía cuidada y un ámbar que funciona como única acción. La demo tenía otro logo, otro ámbar y un violeta que lo teñía todo. Quien hacía clic en «Solicitar demostración» aterrizaba en otro producto.

## Qué decidimos

- **Un logo.** El sol es Solaris. Illarium firma con texto: «un producto de Illarium».
- **Una paleta.** Los colores de la landing pasan a ser tokens con nombre (`ink`, `solar`, `lavanda`, `salvia`, `arcilla`). El producto los copia literalmente. Cada color tiene una sola función: solar es la acción y la evidencia, lavanda la ontología, salvia lo conforme y arcilla el bloqueo.
- **Un espacio de trabajo.** Un repositorio raíz con la documentación compartida y los dos proyectos como submódulos. Cada commit deja anotado qué versión del producto va con qué versión de la landing.

## Qué falló

La cabecera de la demo escondía el indicador de entorno en pantallas estrechas y lo cortaba a 1100 px. Uno de nuestros principios dice que el entorno siempre dice la verdad. Si el usuario no ve «Datos de muestra», ese principio no se cumple. Ahora el indicador se ve en todos los anchos.

## Qué aprendimos

- Comprobamos el contraste de cada par de colores antes de darlo por bueno. El ámbar sirve de fondo, pero no como texto sobre blanco: para eso usamos su versión oscura.
- Un botón que parece apagado hasta que escribes no invita a entrar. Ahora está siempre activo y, si falta el código, te lleva al campo.
