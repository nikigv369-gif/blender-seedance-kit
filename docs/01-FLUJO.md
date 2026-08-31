<!-- © 2026 Nikolas Xes. Todos los derechos reservados. -->

# 01 — El flujo, paso a paso

## 1. Product lock / ficha de personaje

Antes de tocar cualquier generador, escribe una ficha **inmutable** del sujeto. Es
un archivo JSON que vive con el proyecto y cuyo contenido se pega VERBATIM al final
de todo prompt (de imagen y de video).

```json
{
  "producto": "sillón 3 cuerpos",
  "modulos": 3,
  "geometria": "respaldo canaleteado vertical, brazos redondeados",
  "tapiz": "tela gris claro (RGB ~177,176,175)",
  "acentos": "brazos negro azabache (RGB ~26,31,34), franja vertical madera miel (RGB ~222,147,96) al frente de cada brazo",
  "base": "zócalo negro bajo",
  "prohibido": "DO NOT redesign, add, remove, resize or reinterpret the furniture"
}
```

Reglas:

- **Los colores se sacan con análisis real, no a ojo**: kmeans sobre la foto
  (OpenCV) para los 3 clusters dominantes. Un "gris claro" escrito a ojo produce
  otro mueble.
- La línea `prohibido` es obligatoria y va siempre al final.
- Si el sujeto es un **personaje recurrente**, la ficha se genera primero como
  imágenes: frente + espalda + rostro + poses de acción, con vestimenta fija. Todas
  las escenas se generan desde esa ficha. Es el product lock, pero para personas.

## 2. Plan de shots — una intención por shot

Convierte el guion en 3–5 shots de **3–8 segundos**, cada uno con UNA sola
intención. Esto no es estilo: es un límite del modelo (ver
[`02-SEEDANCE-GOTCHAS.md`](02-SEEDANCE-GOTCHAS.md) §14).

Intenciones válidas — elige UNA por shot:

`hero reveal` · `slow orbit` · `texture close-up` · `lateral dolly` ·
`wide establishing` · `float/rise` · `atmósfera (polvo, luz, cortinas)`

Por cada shot anota: intención · duración · imagen de inicio · imagen final (si la
posición de cámara importa) · modelo · costo estimado.

**Cadenas largas**: para tomas de más de ~8s, se pide en **pares de keyframes**
(primer frame + último frame) y el último frame de un clip es el primer frame del
siguiente. Así se encadenan 16s+ de recorrido continuo sin pedirle al modelo una
coreografía que no puede sostener.

## 3. Blockout en Blender ($0, iteración infinita)

Acá se resuelve el movimiento. Ver [`05-BLENDER.md`](05-BLENDER.md).

Lo que el blockout debe entregar:

- Cámara con el recorrido exacto (keyframes lineales, un movimiento por clip).
- Sujeto con el blocking correcto (dónde está, hacia dónde mira, cuándo cruza).
- **Escenografía que calce con las imágenes de referencia.** Si en la foto de
  referencia hay sillas alrededor de una mesa, en el andamio también — si no,
  el modelo inventa dónde ponerlas.
- **Movimiento exagerado.** Los modelos copian movimiento moderado-visible; el
  movimiento sutil lo ignoran por completo. Rango útil: amplio pero lento.

Verificación numérica antes de pagar: replicar el estado de cámara en Python puro
(sin Blender) y comprobar que ningún prop bloquea el rayo cámara→sujeto en ningún
frame.

## 4. QA gate — antes de pagar

**Programático** (OpenCV, keyframe vs foto real):

- correlación de histograma por canal
- similitud de paleta kmeans (ΔE de los 3 clusters dominantes)
- densidad de bordes en la zona del producto

Se reporta como `product_identity / geometry / color`, 0–100.
**Umbral duro: identidad < 90 ⇒ no se genera video.**

**Humano**: abrir la imagen y aprobar. Con 2–3 variantes etiquetadas en un mosaico
horizontal la decisión es más rápida.

Si el keyframe está mal, se rechaza AQUÍ. Regenerar imagen: $0–0.04. Regenerar
video: $0.25–0.84.

## 5. Generación

Ver [`03-PROMPT.md`](03-PROMPT.md) para el formato de prompt y
[`04-COSTOS.md`](04-COSTOS.md) para el presupuesto.

Reglas de gasto:

- Anunciar antes de cada llamada: modelo, duración, costo, acumulado.
- Probar a 3s antes de encargar 5–10s.
- `generate_audio: false` siempre — ahorra ~33% y el audio se hace local.
- fal solo cobra generaciones completadas: un submit fallido o un rechazo por
  política **no cuesta**.
- Pedir un clip de 10s cuando el corte final usa 4s es plata botada.

## 6. Router de fallas — jamás "retry con prompt mejorado"

Cada falla tiene una acción distinta. Volver a mandar el mismo prompt "pero mejor"
es la forma más rápida de quemar presupuesto.

| Falla observada | Acción correcta |
|---|---|
| **PRODUCT_MUTATION** — el sujeto cambió de diseño | Cambiar a un modelo *reference-to-video* con 3–7 referencias reales del sujeto (Kling O1 Reference está hecho para esto) |
| **CAMERA_WRONG** — el movimiento no es el pedido | Fijar first+last frame. NO re-promptear |
| **EXCESSIVE_MOTION** — se deforma por moverse mucho | Bajar el presupuesto de movimiento: una intención, verbos suaves (`gently`, `slowly`) |
| **BAD_ENVIRONMENT** — fondo o entorno feo | Regenerar el KEYFRAME local ($0), no el video |
| **TEXT_ERROR** — letras o números deformes | Sacar el texto del prompt. El texto va en el montaje, siempre |
| **Los objetos "caen" en vez de armarse** | Límite estructural de la difusión. La coreografía precisa se hace local (motor de física/animación en el montaje), no con más intentos |
| **Alucinación por prompt "creativo"** (`psychedelic`, `warp`, `surreal`, `backrooms`) | Esas palabras SON la orden de alucinar. Prompt sobrio + el FX psicodélico local en post |
| **Boca moviéndose mal ("cantando")** | El modelo no oye el audio. Nunca pedir `singing`/`mouthing`: el lip-sync no existe en i2v |
| **Morfosis fea con `--end-image`** | El par no era continuación real. `end-image` solo si es el MISMO plano un paso después; si no, single-image |

## 7. Montaje (local, $0)

Texto, precio, logo, captions, música y FX: todo local. Nunca del generador.

- El clip de Seedance sale a **24 fps**; si el andamio va a 30 fps hay que
  conformar al montar.
- Si se usó la técnica de guía estirada (ver `02` §12), acá se acelera el clip para
  recuperar la velocidad original.
