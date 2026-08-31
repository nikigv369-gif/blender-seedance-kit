<!-- © 2026 Nikolas Xes. Todos los derechos reservados. -->

# 06 — Bitácora del modelo

Novedades de Seedance que afectan a este pipeline, con fecha. Cada entrada dice qué
cambia y qué hay que probar antes de generalizar.

## 2026-04 — Seedance 2.0 en fal.ai

Sucesor directo de Seedance 1.0 Pro. Es el que usan estos scripts.

- Audio generado nativo junto con el video (sin doblar SFX después). Igual lo
  dejamos en `false`: ahorra ~33% y el audio se hace local.
- Control de cámara tipo director: dolly zoom, rack focus, tracking shots, POV.
- Duraciones 4–15s, más aspect ratios incluido 9:16.
- Generación en menos de 2 min.

`bytedance/seedance-2.0/reference-to-video` · `bytedance/seedance-2.0/image-to-video`

## 2026-07-31 — Seedance 2.5

Sucesor directo de 2.0, mismo precio y plan, sin espera de acceso.

- Clips nativos de **30s** (el doble).
- Hasta **4K**.
- Hasta **50 imágenes de referencia** por generación (antes 12) → permite lockear un
  producto con muchos más ángulos en una sola llamada.
- Edición *redraw anything* localizada por frame.
- Sonido estéreo nativo.

**Cómo migrar:** es un swap de endpoint (`bytedance/seedance-2.5/...`). Antes de
generalizar, correr un caso ya conocido y comparar contra el resultado de 2.0 — los
gotchas de `docs/02` no están verificados en 2.5.
