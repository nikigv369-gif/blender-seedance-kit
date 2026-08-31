<!-- © 2026 Nikolas Xes. Todos los derechos reservados. -->

# 02 — Seedance en fal.ai: bugs y límites reales

Todo lo de acá está **verificado contra la API real**, no sacado de la
documentación. Varios de estos hallazgos costaron generaciones pagadas.

## Endpoint y transporte

**1. El endpoint va SIN el prefijo `fal-ai/`.**

```
OK   bytedance/seedance-2.0/reference-to-video
MAL  fal-ai/bytedance/seedance-2.0/reference-to-video
```

Con el prefijo malo la cola **acepta el request y lo marca COMPLETED al instante**
(`inference_time` ~0.02s) sin generar nada. No cobra, pero se pierde el viaje y
parece que funcionó. Ojo: Kling **sí** lleva el prefijo `fal-ai/`; es fácil calcarlo.

**2. Las URLs de status/result usan solo `owner/alias`:**

```
queue.fal.run/bytedance/seedance-2.0/requests/{request_id}[/status]
```

Sin el subpath `/reference-to-video`. Regla práctica: usar siempre los
`status_url` / `response_url` que devuelve el submit, nunca construirlas a mano.

**3. El 422 del result trae el detalle en el body.** Leerlo con `e.read()` antes de
reintentar — reintentar a ciegas repite el mismo error.

**4. Nombres de campo distintos por endpoint.** Seedance y Kling usan
`image_url` / `end_image_url`; Veo usa `first_frame_url` / `last_frame_url`. Con el
nombre equivocado la cola responde COMPLETED y el result tira 422: no genera y no
cobra.

## Política de contenido

**5. Rechaza caras humanas fotorrealistas** (`content_policy_violation` /
`partner_validation_failed`). Es la política anti-deepfake de ByteDance y está
**documentada como regla del sistema**, no es un bug ni azar: bloquea todo rostro
fotorrealista en las referencias, aunque la imagen sea generada por IA.

- Re-encodear o quitar metadata C2PA **no lo arregla** — es detección de cara.
- Pasan: caras chicas o lejanas en el encuadre, estilos chibi/cartoon.
- Para cara fotorrealista de una persona real, usar otro modelo (Kling la acepta).
- Los rechazos por política **no cobran**.

**6. Nunca declarar en el prompt que un personaje está basado en una persona
real.** Aunque el estilo cartoon pase el filtro, escribir "based on my father / a
real person" puede gatillar la política de likeness. Describirlo siempre como
100% ficticio: "a fictional chibi carpenter character".

## Comportamiento del modelo

**7. La lista FORBIDDEN nunca debe llevar una frase "no [X]" cuando X es algo que
SÍ quieres.** Este bug costó reintentos con plata real:

```
FORBIDDEN: static locked-off camera, no camera movement, ...
                                     ^^^^^^^^^^^^^^^^^^^
```

Esa segunda frase le prohíbe al modelo el movimiento de cámara — exactamente lo
opuesto a lo pedido arriba en el bloque SHOT (`camera orbits...`). Resultado: video
casi estático.

**No existe** parámetro numérico de *influence weight* o *strength* en la API
(revisado el repo oficial). El control es **100% por texto del prompt**, así que
una sola frase contradictoria puede anular un bloque entero de instrucciones.

> Regla dura: releer la lista FORBIDDEN palabra por palabra antes de enviar,
> buscando negaciones de cosas pedidas arriba.

**8. Un clip = una idea de cámara.** Convergen cuatro fuentes independientes
(documentación oficial de fal, blogs de vendors, guías chinas de la comunidad,
foros técnicos):

- "Use only one primary camera instruction; multiple conflicting movements cause
  jitter" + separar la descripción del movimiento de cámara de la del sujeto.
- El video-referencia rinde mejor entre 3–8s; sobre 10s el modelo duda de qué
  priorizar.
- Primer plano + rotación grande = se rompe la cara. Movimiento simultáneo en los
  tres ejes rompe la consistencia.
- Para algo más largo: **generar por segmentos y montar en edición**, usando el
  último frame de un clip como referencia del siguiente.

Consecuencia económica: partir en 3 clips de ~5s cuesta **lo mismo** que un clip de
15s (se cobra por segundo), pero reintentar uno malo cuesta un tercio.

**9. El video-guía debe EXAGERAR el movimiento.** El modelo copia movimiento
moderado-visible; el sutil lo ignora (un vaivén suave del andamio produjo un
personaje muerto). Movimiento rápido, en cambio, produce glitches. Rango útil:
**amplio pero lento**, un solo movimiento de cámara por clip.

**10. Técnica de la guía estirada.** Si la coreografía tiene más de un movimiento y
no se puede partir, se **estira el andamio 1.5x hasta 15s** (el máximo de
video-referencia) escalando *todos* los frames y períodos —fases, strides,
ráfagas, blends, escala de ruido—, y el clip generado **se acelera 1.5x en post**
recuperando la velocidad original. Movimientos más lentos son más legibles para el
modelo. El costo sube proporcional a la duración.

Aun así: estirar **no** arregla el subpeso de movimiento. Lo que corresponde de
verdad es partir en clips de una idea.

## Límites y formatos

**11. Límites oficiales por generación:** hasta 9 imágenes · 3 videos (2–15s en
total) · 3 audios (15s c/u) · 12 archivos.
Consejo de la comunidad: **empezar mínimo** — una referencia fuerte, e ir agregando.

**12. Devuelve 24 fps**, no 30 (verificado con `ffprobe` en todos los outputs). Si
el andamio de Blender va a 30 fps, hay que tenerlo en cuenta al conformar en post.

**13. El 1080p es detalle real, no un upscale.** Verificado con datos, no con
teoría: un round-trip 1080→720→1080 sobre un frame pagado da **PSNR 39.7 dB**,
mientras la firma de un upscale conocido (720p real subido con lanczos) da
**49.2 dB**. Esos ~10 dB de diferencia significan que el 1080p contiene alta
frecuencia que un 720p no puede cargar. (El model card dice "480p y 720p nativos",
pero el archivo real del endpoint de fal lo contradice.) Vale la pena pagar 1080p
cuando es para portafolio.

## Versiones

- **2.0** — el que usan estos scripts. Audio nativo, control de cámara tipo
  director, 4–15s, 9:16 disponible.
- **2.5** (jul-2026) — clips nativos de 30s, hasta 4K, hasta 50 imágenes de
  referencia por generación, edición localizada por frame, sonido estéreo nativo.
  Es un swap de endpoint; probar con un caso conocido antes de generalizar.
