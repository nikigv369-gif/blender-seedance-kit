# -*- coding: utf-8 -*-
# (c) 2026 Nikolas Xes. Todos los derechos reservados.
#
# Saca una muestra de TELA plana desde la foto real del producto, para vestir el
# modelo 3D de build_product_3d.py. Aplana la iluminacion (divide por su propio
# blur) re-anclando media y desviacion por canal para no lavar las telas oscuras.
#
#   python scripts/fabric_swatch.py --src foto.jpg --out tela.png --cx 0.50 --cy 0.66
#
# --grid escribe un contact sheet con parches candidatos numerados para ELEGIR
# mirando, en vez de adivinar coordenadas (ver docs/05-BLENDER.md).
#
# OJO: no espejar 2x2 para hacerla tileable — en motivos reconocibles produce
# efecto caleidoscopio. La costura se mata en Blender con projection BOX +
# projection_blend alto (0.85), que es lo que hace build_product_3d.py.

import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def flatten_light(arr, blend=0.6):
    """Quita el degradado de iluminacion SIN levantar los negros: divide por su
    propio blur, mezcla parcial con el original, y devuelve media/contraste
    (mean/std por canal) a los valores reales de la foto."""
    src = arr.astype(np.float32)
    img = Image.fromarray(arr)
    blur = np.asarray(img.filter(ImageFilter.GaussianBlur(radius=90))).astype(np.float32)
    blur = np.clip(blur, 12, None)
    flat = src / blur * src.mean(axis=(0, 1), keepdims=True)
    out = flat * blend + src * (1.0 - blend)

    # re-anclar mean/std por canal al original (si no, la tela oscura se aclara)
    for c in range(3):
        s_mean, s_std = src[:, :, c].mean(), src[:, :, c].std()
        o_mean, o_std = out[:, :, c].mean(), out[:, :, c].std()
        if o_std > 1e-3:
            out[:, :, c] = (out[:, :, c] - o_mean) * (s_std / o_std) + s_mean
    return np.clip(out, 0, 255).astype(np.uint8)


def crop_patch(a, fx, fy, frac):
    h, w = a.shape[:2]
    side = int(min(w, h) * frac)
    cx, cy = int(w * fx), int(h * fy)
    l = max(0, min(w - side, cx - side // 2))
    t = max(0, min(h - side, cy - side // 2))
    return a[t:t + side, l:l + side, :3], side, (cx, cy)


def contact_sheet(a, frac, out_path, cols=4, rows=4):
    """Grid de parches candidatos numerados con sus coordenadas relativas, para
    elegir la zona de tela pura mirando en vez de adivinar."""
    h, w = a.shape[:2]
    cell = 220
    sheet = Image.new("RGB", (cols * cell, rows * cell), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    for r in range(rows):
        for c in range(cols):
            fx = (c + 0.5) / cols
            fy = (r + 0.5) / rows
            patch, _, _ = crop_patch(a, fx, fy, frac)
            tile = Image.fromarray(patch).resize((cell, cell), Image.LANCZOS)
            sheet.paste(tile, (c * cell, r * cell))
            draw.text((c * cell + 6, r * cell + 6),
                      "%.2f %.2f" % (fx, fy), fill=(255, 230, 0))
    sheet.save(out_path)
    print("grid ->", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="foto real del producto")
    ap.add_argument("--out", help="PNG de salida (1024x1024)")
    ap.add_argument("--cx", type=float, default=0.50, help="centro X relativo (0-1)")
    ap.add_argument("--cy", type=float, default=0.66, help="centro Y relativo (0-1)")
    ap.add_argument("--frac", type=float, default=0.26,
                    help="lado del parche como fraccion del lado menor de la foto")
    ap.add_argument("--blend", type=float, default=0.6,
                    help="cuanto se aplana la iluminacion (0 = nada, 1 = todo)")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--grid", help="escribe un contact sheet de candidatos y termina")
    args = ap.parse_args()

    a = np.array(Image.open(args.src).convert("RGB"))

    if args.grid:
        contact_sheet(a, args.frac, args.grid)
        return

    if not args.out:
        raise SystemExit("Falta --out (o usa --grid para elegir la zona primero)")

    patch, side, center = crop_patch(a, args.cx, args.cy, args.frac)
    patch = flatten_light(patch, blend=args.blend)

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    Image.fromarray(patch).resize((args.size, args.size), Image.LANCZOS).save(args.out)
    print("OK", args.out, "desde parche de", side, "px en", center)


if __name__ == "__main__":
    main()
