<!-- © 2026 Nikolas Xes. Todos los derechos reservados. -->

# 03 — La receta de prompt

## El prompt NO va en JSON

Alguien te va a decir que JSON es mejor. Para este caso, la evidencia dice que no:

- La guía oficial de fal.ai: *Seedance 2.0 follows plain natural language*.
- Las guías chinas de la comunidad usan **prosa con secciones etiquetadas**
  (【estilo】【línea de tiempo】【sonido】【referencias】) y segmentación por tiempo.
  No llaves JSON.
- La fórmula de 6 pasos de la guía oficial es en prosa, 60–100 palabras.
- Advertencia de un test A/B real: *"Complex JSON actually performs worse than a
  clean bullet timeline, because the model gets swamped."*

El modelo tokeniza igual: JSON no es un upgrade mágico. Único caso donde ayuda:
3+ tomas con cortes que deben mantener consistencia, control independiente de
audio+luz+cámara+estilo, o un template reusable programático.

## Estructura que sí funciona

### 1. Declarar QUÉ se toma de cada referencia

Este es **el error #1 de la comunidad**: escribir solo "use @Video1". Cada `@ref`
debe declarar explícitamente qué aporta.

```
@Video1 muestra el movimiento de cámara y el blocking del personaje.
@Image1 muestra la apariencia exacta del personaje.
@Audio1 es la referencia de BGM.
```

En inglés, como lo escribe la guía: *reference @video1's camera work* /
*reference @video1's motion* / *reference @image1's character look*.

### 2. Segmentar por tiempo, una acción por segmento

Una acción y **un** movimiento de cámara por segmento:

```
0-3s: el personaje entra desde la izquierda, la cámara hace un dolly lento hacia adelante.
3-6s: el personaje se detiene y mira hacia arriba, la cámara sube en pedestal.
```

Vocabulario técnico de cine —`dolly`, `pan`, `orbital`, `rack focus`,
`pedestal`— nunca descripciones vagas.

### 3. Línea de estilo global AL FINAL

Iluminación, paleta, textura de imagen, referencia fotográfica. Al final, no
mezclada con las acciones.

### 4. Product lock verbatim

La línea `prohibido` de la ficha, sin editar, cerrando el prompt.

## Plantilla

```
@Video1 provides the camera movement and subject blocking.
@Image1 provides the exact appearance of the subject.

0-3s: <una acción> · <un movimiento de cámara>
3-6s: <una acción> · <un movimiento de cámara>

Style: <iluminación> <paleta> <textura/grano> <referencia fotográfica>.

DO NOT redesign, add, remove, resize or reinterpret the subject.
```

## Palabras prohibidas

`psychedelic` · `warp` · `surreal` · `backrooms` · `dreamlike` · `trippy`

No son estilo: son **la orden de alucinar**. Si quieres ese look, prompt sobrio y
el FX se aplica local en el montaje.

Tampoco: texto, números, letreros, precios, logos, `singing`, `mouthing`.

## Antes de enviar — checklist

- [ ] ¿Cada `@ref` dice qué aporta?
- [ ] ¿Hay UNA sola idea de cámara?
- [ ] ¿La lista FORBIDDEN niega algo que pediste arriba? (ver `02` §7)
- [ ] ¿El product lock va verbatim al final?
- [ ] ¿Hay texto o números pedidos al modelo? Sácalos.
- [ ] ¿La duración es la que realmente vas a usar en el corte?
