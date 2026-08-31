<!-- © 2026 Nikolas Xes. Todos los derechos reservados. -->

# blender-seedance — motor de video IA con andamio 3D

Pipeline para generar tomas de video fotorrealistas **controlando la cámara y el
blocking**, en vez de rogarle a un modelo de texto-a-video que adivine lo que
quieres.

La idea central en una línea:

> **Blender pone el movimiento. Seedance pone los píxeles.**

Renderizas en Blender un *blockout* (geometría gris, sin textura) con la cámara y
el personaje/producto moviéndose exactamente como quieres. Ese clip feo lo mandas
a Seedance 2.0 `reference-to-video` junto con una imagen de identidad, y el modelo
lo repinta fotorrealista **respetando tu coreografía**.

Por qué importa: el control de cámara es el problema no resuelto de los modelos de
video. Prompts como "orbital shot que termina en primer plano" salen distintos cada
vez y cuestan plata cada intento. Un andamio de Blender cuesta $0, se itera en
segundos y es determinista.

```
        ┌──────────────────┐
FOTO/   │ 1. PRODUCT LOCK  │  ficha inmutable del sujeto (colores por kmeans,
IDEA ──►│    o ficha de    │     geometría, "prohibido redesign") — va VERBATIM
        │    personaje     │     al final de todo prompt
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │ 2. BLOCKOUT      │  Blender headless: cámara + sujeto animados por
        │    (Blender, $0) │  código. Iterar acá es gratis.
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │ 3. KEYFRAME      │  imagen de identidad (foto real o generada local).
        │    (gate barato) │  Si el sujeto está mal, SE RECHAZA AQUÍ.
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │ 4. SEEDANCE      │  reference-to-video: @Video1 = movimiento,
        │    (paga)        │  @Image1 = apariencia. UNA idea de cámara por clip.
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │ 5. MONTAJE       │  texto, precio, logo, captions, música: TODO local.
        │    (local, $0)   │  Nunca se le pide texto al modelo de video.
        └──────────────────┘
```

## Las 5 reglas que no se negocian

1. **El modelo de video no diseña la toma. Solo anima algo ya aprobado.**
   Todo lo que se pueda resolver local (imagen, texto, montaje) se resuelve local
   a $0. La IA de video se paga SOLO por movimiento imposible de simular.
2. **Un clip = una idea de cámara.** "Camina + llega + gira + revela" en un solo
   prompt garantiza deformación. Tres clips de 5s cuestan lo mismo que uno de 15s,
   pero reintentar uno malo cuesta un tercio.
3. **Nunca texto ni números en el prompt de video.** Salen deformes siempre. El
   texto va en el montaje.
4. **Se rechaza en el keyframe, no en el video.** Regenerar una imagen local cuesta
   $0. Regenerar un clip cuesta $0.25–$0.84.
5. **Cuando algo sale mal, no se re-promptea: se cambia de herramienta.**
   Ver el router de fallas en [`docs/01-FLUJO.md`](docs/01-FLUJO.md).

## Documentación

| Doc | Qué hay adentro |
|---|---|
| [`docs/01-FLUJO.md`](docs/01-FLUJO.md) | El pipeline paso a paso + router de fallas (qué hacer con cada tipo de error) |
| [`docs/02-SEEDANCE-GOTCHAS.md`](docs/02-SEEDANCE-GOTCHAS.md) | Bugs y límites reales del endpoint, verificados pagando |
| [`docs/03-PROMPT.md`](docs/03-PROMPT.md) | La receta de prompt que funciona (y por qué JSON no sirve acá) |
| [`docs/04-COSTOS.md`](docs/04-COSTOS.md) | Fórmula de precio y la trampa que puede convertir un clip en $12 |
| [`docs/05-BLENDER.md`](docs/05-BLENDER.md) | Blender headless: el andamio, modelar producto por código, gotchas |
| [`docs/06-BITACORA-MODELO.md`](docs/06-BITACORA-MODELO.md) | Qué cambió en cada versión de Seedance y cómo migrar |

## Setup

```bash
python -m venv venv
venv/Scripts/pip install -r requirements.txt
cp .env.example .env    # y pega tu FAL_KEY de fal.ai
```

Blender aparte (3.x/4.x), invocable como `blender` en el PATH. Los scripts de
render corren headless (`-b`), no necesitan abrir la GUI.

## Uso mínimo

```bash
# 1. blockout: 5s, cámara orbitando 90°, vertical 1080x1920
blender -b --python scripts/render_shot.py -- --out shots/test01_blockout.mp4 --angle 0

# 2. repintado fotorrealista
venv/Scripts/python scripts/seedance_shot.py \
  --video shots/test01_blockout.mp4 \
  --image character_refs/test01.png \
  --prompt "Escena cinematografica, iluminacion dramatica, estilo realista" \
  --out shots/test01_final.mp4
```

## Scripts

| Script | Qué hace |
|---|---|
| `scripts/render_shot.py` | Blockout genérico: silueta humanoide + cámara orbital. El andamio de arranque. |
| `scripts/seedance_shot.py` | Llamada simple a Seedance vía `fal_client` (blockout + 1 imagen de identidad). |
| `scripts/fal_seedance.py` | Cliente completo sin dependencias: hasta 9 imágenes, 3 videos, 3 audios de referencia, `--end-image`, control de resolución y duración. El que se usa en producción. |
| `scripts/build_product_3d.py` | Modela un producto en 3D **por código** (cajas con bevel grueso + subsurf = volumen mullido) y lo viste con la tela sacada de una foto real. Para giros 360 de producto sin comprar modelos. |
| `scripts/fabric_swatch.py` | Extrae y aplana la muestra de tela desde la foto del producto, para texturizar el modelo. |
