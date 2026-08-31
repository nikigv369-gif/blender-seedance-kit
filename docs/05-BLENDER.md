<!-- © 2026 Nikolas Xes. Todos los derechos reservados. -->

# 05 — Blender: el andamio y el producto por código

Blender acá no se usa para hacer arte. Se usa para dos cosas:

1. **El andamio (blockout)** — geometría gris que le dice al modelo de video cómo se
   mueve la cámara y dónde está el sujeto.
2. **El producto en 3D real** — cuando necesitas un giro 360 de un objeto y solo
   tienes fotos.

Ambas cosas corren **headless** (`blender -b`), sin abrir la GUI, y cuestan $0.

---

## Parte 1 — El andamio

`scripts/render_shot.py` es el andamio mínimo: silueta humanoide de primitivas
(torso cilindro, cabeza esfera, brazos y piernas) parentada a un empty, más una
cámara con constraint `TRACK_TO` sobre un pivot que rota. Dos keyframes lineales y
listo.

```bash
blender -b --python scripts/render_shot.py -- --out shots/test01_blockout.mp4 --angle 0
blender -b --python scripts/render_shot.py -- --out shots/test02_blockout.mp4 --angle 120
```

Render con EEVEE, 1080×1920, 30 fps, H.264.

### Qué tiene que cumplir un buen andamio

- **Un solo movimiento de cámara.** Ver `02` §8.
- **Movimiento exagerado, amplio pero lento.** El modelo ignora lo sutil y
  glitchea con lo rápido. Ver `02` §9.
- **Escenografía que calce con las imágenes de referencia.** Si la referencia
  tiene sillas alrededor de una mesa, el andamio también las lleva — si no, el
  modelo inventa dónde ponerlas.
- **Línea de visión libre.** Verificar numéricamente (replicando el estado de
  cámara en Python puro, sin Blender) que ningún prop bloquee el rayo
  cámara→sujeto en ningún frame. Descubrirlo después de pagar es caro.

### Gotchas de Blender headless

**1. `--out` debe ser ruta absoluta.** Con ruta relativa, Blender **crea las
carpetas pero no escribe la animación, y no avisa**. Sin un `.blend` guardado,
Blender resuelve rutas relativas de forma ambigua y no siempre respeta el cwd del
proceso. Por eso `render_shot.py` ancla todo a la carpeta del proyecto:

```python
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isabs(args.out):
    args.out = os.path.join(PROJECT_ROOT, args.out)
```

**2. Los argumentos van después de `--`.** Todo lo anterior se lo come Blender.
El patrón es siempre:

```python
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
```

**3. El engine cambió de nombre.** En Blender 4.2+ es `BLENDER_EEVEE_NEXT`, no
`BLENDER_EEVEE`. Con el nombre viejo tira excepción en 4.2+.

**4. Interpolación de keyframes.** Blender interpola con bezier por defecto, lo que
mete ease-in/ease-out. Para un movimiento de cámara constante y legible hay que
forzar `LINEAR` a mano en todas las fcurves.

**5. 30 fps en el andamio, 24 fps a la salida.** Seedance devuelve 24 fps.
Conformar en el montaje.

---

## Parte 2 — El producto en 3D, modelado por código

**No hace falta un modelo 3D comprado ni IA.** Se modela por código y se viste con
una muestra de la textura sacada de la foto real. Costo $0, ~45s de render para 60
frames con EEVEE.

```bash
blender -b -P scripts/build_product_3d.py -- --tela tela.png --out DIR --name v1 --frames 150
```

### Por qué no comprar "foto a 3D"

Los GLB baratos de servicios "foto a 3D" **no son modelos 3D**: son cajas con las
fotos proyectadas en las caras. En un render de prueba se ve el piso de baldosas y
el watermark del teléfono calcados sobre el objeto. Cualquier giro se ve a cartón.

> **Verifica SIEMPRE un modelo 3D ajeno con un render de prueba antes de construir
> nada encima.** Un GLB que pesa poco y viene de "foto a 3D" suele ser una caja
> texturizada.

### La técnica: volumen mullido por modificadores

Para muebles tapizados, cojines, almohadas y cualquier cosa blanda:

```
cubo → BEVEL (width ~0.11, segments 6, limit ANGLE) → SUBSURF (levels 2)
```

Eso solo ya da un cojín creíble. El volumen mullido nace ahí; el remesh posterior
solo suelda los cojines entre sí. Se arma el objeto completo como una pila de
bloques con esas dos operaciones aplicadas.

### La tela: sacarla de la foto

`scripts/fabric_swatch.py` extrae la muestra. Cuatro reglas que salieron de que no
funcionara:

1. **Elegir la zona mirando un grid de parches candidatos**, no adivinando
   coordenadas. Zona de tela pura: sin sombras de unión, sin bordes, sin costuras.
2. Al **aplanar la iluminación** de la muestra (dividirla por su propio blur),
   **re-anclar media y desviación por canal al original**. Si no, las telas oscuras
   salen lavadas.
3. **No espejar 2×2 para hacerla tileable.** En motivos reconocibles produce efecto
   caleidoscopio y se nota al instante.
4. En vez de eso: **motivo grande + `projection: BOX` con `projection_blend` alto
   (0.85)**. Eso mata la costura sin espejar.

### Cuándo usar esto y cuándo no

- **Giro 360 de producto, hook visual, ángulo que no tienes fotografiado** → esto.
- **Textura fina, materiales complejos, escena completa** → mejor keyframe local +
  Seedance.

El modelo 3D también sirve como **andamio** del punto 1: renderizas el giro en gris,
lo mandas como `@Video1` y Seedance lo repinta con la foto real como `@Image1`.
