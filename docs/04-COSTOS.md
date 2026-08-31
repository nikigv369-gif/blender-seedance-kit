<!-- © 2026 Nikolas Xes. Todos los derechos reservados. -->

# 04 — Costos: la fórmula y la trampa

Precios verificados contra las fichas de fal en **agosto 2026**. Cambian; verificar
antes de lanzar una tanda grande.

## Fórmula de Seedance 2.0

```
tokens = (alto × ancho × (dur_input + dur_output) × 24) / 1024
costo  = tokens × $0.014 / 1000        ($0.008 / 1000 en 4k)
```

Nota crítica en `dur_input`: **la duración del video de referencia entra en la
fórmula**. Ver la trampa más abajo.

Resultado práctico en 9:16:

| Config | Precio |
|---|---|
| 1080p sin video de referencia | **$0.6804/s** |
| 1080p con video de referencia (×0.6) | **$0.4082/s** |
| Fast / Mini (tope 720p) con video ref | **$0.1452/s** |
| 720p std con video ref | **$0.1814/s** |

## ⚠ La trampa

**El video de referencia se cobra igual que el output.**

Mandar los 15s completos de un blockout de Blender para generar un clip de 15s en
1080p:

```
(1920 × 1080 × (15 + 15) × 24) / 1024 = 1.458.000 tokens → ~$12.25 por UN clip
```

**Recortar la referencia a 2–3s es obligatorio.** El andamio se renderiza completo
para revisarlo local (gratis), pero a la API solo se manda el tramo que el modelo
necesita para entender el movimiento.

## Otros modelos, para comparar

| Modelo | Precio | 1080p real |
|---|---|---|
| **Veo 3.1** first-last-frame | $0.20/s (audio off) | Sí — `resolution` 720p/1080p/4k, dur 4/6/8s, sale a 24 fps |
| **Seedance 2.0** ref-to-video / i2v | ver fórmula | Sí — param explícito; i2v acepta `end_image_url` |
| **Kling O1 Reference** | $0.112/s | No — sin parámetro de resolución (la familia mide 720×1280 en disco). Pero hasta 7 imágenes de referencia fusionadas en representación 3D del objeto: es el mejor para **identidad de producto** |
| **Kling 3.0 Std** i2v | $0.084/s | No — bueno para cámara sobre espacio real (dolly, orbit, atmósfera) |
| **Hailuo 2.3 Pro** | $0.49 fijo | Sí, pero schema mínimo (`image_url` + `prompt`): **no acepta product lock** |
| **Seedance Fast/Mini** | $0.1452/s con video ref | No, tope 720p — sirve para tests botables |

Imágenes (keyframes, letras, outpaint) con Stable Diffusion local: **$0**.
Montaje, texto, precio, logo, FX, captions: **$0**.

## Reglas de gasto

1. **Anunciar antes de cada llamada**: modelo, duración, costo estimado, acumulado.
2. Presupuesto por video: fijar un techo antes de empezar y respetarlo.
3. Probar a 3s antes de encargar 5–10s.
4. `generate_audio: false` siempre — ahorra ~33%.
5. fal solo cobra **generaciones completadas**. Un submit fallido, un 422 o un
   rechazo por política no cuestan.
6. Un clip de 10s cuando el corte final usa 4s es plata botada. Pedir corto.
7. Recortar SIEMPRE el video de referencia (ver la trampa).
