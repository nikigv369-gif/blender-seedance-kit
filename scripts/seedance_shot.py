# © 2026 Nikolas Xes. Todos los derechos reservados.
"""
Sube el blockout de Blender (cámara/movimiento) + una imagen de referencia (identidad del
personaje) a fal.ai y llama a Seedance 2.0 reference-to-video para repintar el plano fotorreal.

Uso:
  venv\\Scripts\\python scripts\\seedance_shot.py ^
    --video shots\\test01_blockout.mp4 ^
    --image character_refs\\test01.png ^
    --prompt "Escena cinematografica, iluminacion dramatica, estilo realista" ^
    --out shots\\test01_final.mp4
"""
import argparse
import os
import sys
import urllib.request

from dotenv import load_dotenv
import fal_client

MODELS = {
    "fast": "bytedance/seedance-2.0/fast/reference-to-video",
    "std": "bytedance/seedance-2.0/reference-to-video",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, help="blockout renderizado en Blender")
    p.add_argument("--image", required=True, help="imagen de referencia de identidad del personaje")
    p.add_argument("--prompt", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--model", choices=list(MODELS), default="fast")
    p.add_argument("--resolution", default="720p")
    p.add_argument("--duration", default="5")
    p.add_argument("--aspect-ratio", default="9:16")
    return p.parse_args()


def on_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(f"[fal] {log['message']}")


def main():
    load_dotenv()
    if not os.environ.get("FAL_KEY"):
        sys.exit("Falta FAL_KEY. Copia .env.example a .env y pega tu key de fal.ai ahi.")

    args = parse_args()

    print(f"[seedance] subiendo {args.video}")
    video_url = fal_client.upload_file(args.video)
    print(f"[seedance] subiendo {args.image}")
    image_url = fal_client.upload_file(args.image)

    prompt = f"@Video1 muestra el movimiento de camara y el blocking del personaje. @Image1 muestra la apariencia exacta del personaje. {args.prompt}"

    model_id = MODELS[args.model]
    print(f"[seedance] llamando {model_id}")
    result = fal_client.subscribe(
        model_id,
        arguments={
            "prompt": prompt,
            "video_urls": [video_url],
            "image_urls": [image_url],
            "resolution": args.resolution,
            "duration": args.duration,
            "aspect_ratio": args.aspect_ratio,
        },
        with_logs=True,
        on_queue_update=on_update,
    )

    video_result_url = result["video"]["url"]
    print(f"[seedance] resultado: {video_result_url}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    urllib.request.urlretrieve(video_result_url, args.out)
    print(f"[seedance] guardado -> {args.out}")
    print("[seedance] revisa el costo real en https://fal.ai/dashboard/billing (reference-to-video no esta en la tabla de precios ya investigada)")


if __name__ == "__main__":
    main()
