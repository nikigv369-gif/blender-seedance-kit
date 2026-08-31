# © 2026 Nikolas Xes. Todos los derechos reservados.
# Genera video con Seedance 2.0 reference-to-video (fal.ai) — acepta hasta 9
# imágenes, 3 videos y 3 audios como referencia (@Image1, @Video1, @Audio1 en
# el prompt). Con video-referencia el precio baja 40% ($0.1814/s en 720p std).
#
# Uso:
#   set FAL_KEY=tu-key   (o en el .env de la raiz del proyecto)
#   venv/Scripts/python.exe scripts/fal_seedance.py --images img1.png,img2.png \
#     --videos clip1.mp4 --audios voz.wav --prompt "..." --dur 3 --out out.mp4
import argparse, base64, json, mimetypes, os, sys, time, urllib.error, urllib.request

# OJO: el endpoint de Seedance va SIN prefijo "fal-ai/" (a diferencia de Kling).
# Con el prefijo, la queue acepta el request pero el modelo nunca corre
# (inference_time ~0.02s, response 404) — bug diagnosticado 2026-07-21.
MODEL = "bytedance/seedance-2.0/reference-to-video"


def load_key():
    if os.environ.get("FAL_KEY"):
        return os.environ["FAL_KEY"]
    env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.strip().startswith("FAL_KEY="):
                return line.strip().split("=", 1)[1]
    sys.exit("Falta FAL_KEY: exportala o ponla en el .env de la raiz del proyecto")


def api(url, key, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Key {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    return f"data:{mime};base64,{b64}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--images", default="", help="rutas separadas por coma -> @Image1, @Image2...")
    ap.add_argument("--videos", default="", help="rutas separadas por coma -> @Video1, @Video2...")
    ap.add_argument("--audios", default="", help="rutas separadas por coma -> @Audio1, @Audio2...")
    ap.add_argument("--dur", default="4", choices=[str(x) for x in range(4, 16)] + ["auto"])
    ap.add_argument("--resolution", default="720p", choices=["480p", "720p", "1080p", "4k"])
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--generate-audio", action="store_true", help="deja que Seedance genere su propio audio (default: off, usamos @Audio1 solo de guía)")
    ap.add_argument("--end-image", help="último frame (usa el endpoint image-to-video, no reference-to-video)")
    args = ap.parse_args()

    key = load_key()
    payload = {
        "prompt": args.prompt,
        "resolution": args.resolution,
        "duration": args.dur,
        "aspect_ratio": args.aspect,
        "generate_audio": bool(args.generate_audio),
        "bitrate_mode": "high",
    }
    # primer+último frame vive en otro endpoint: image-to-video, con image_url
    # singular. reference-to-video (el default) NO acepta end_image_url.
    if args.end_image:
        if not args.images:
            sys.exit("--end-image necesita --images con el primer frame")
        primera = args.images.split(",")[0].strip()
        payload["image_url"] = data_uri(primera)
        payload["end_image_url"] = data_uri(args.end_image)
        args.images = ""
    if args.images:
        payload["image_urls"] = [data_uri(p.strip()) for p in args.images.split(",") if p.strip()]
    if args.videos:
        payload["video_urls"] = [data_uri(p.strip()) for p in args.videos.split(",") if p.strip()]
    if args.audios:
        payload["audio_urls"] = [data_uri(p.strip()) for p in args.audios.split(",") if p.strip()]

    # tokens = (alto*ancho*(dur_input+dur_output)*24)/1024 a $0.014/1000 tokens.
    # 720p 9:16 da $0.3024/s, y cada resolución escala por su conteo de píxeles.
    PIX = {"480p": 480 * 854, "720p": 720 * 1280, "1080p": 1080 * 1920, "4k": 2160 * 3840}
    price_per_s = PIX[args.resolution] * 24 / 1024 / 1000 * (0.008 if args.resolution == "4k" else 0.014)
    if args.videos:
        price_per_s *= 0.6  # el descuento aplica, pero el video de entrada también se cobra
    dur_n = int(args.dur) if args.dur != "auto" else 5
    print(f"Costo aprox: ${price_per_s * dur_n:.2f} de output ({args.dur}s @ {args.resolution})"
          + (" + los segundos del video de referencia al mismo precio" if args.videos else ""))

    endpoint = "bytedance/seedance-2.0/image-to-video" if args.end_image else MODEL
    queue = f"https://queue.fal.run/{endpoint}"
    job = api(queue, key, payload)
    status_url = job["status_url"]
    resp_url = job["response_url"]
    print(f"En cola: {job.get('request_id')}")

    while True:
        st = api(status_url, key)
        s = st.get("status")
        print("  estado:", s)
        if s == "COMPLETED":
            break
        if s in ("FAILED", "ERROR"):
            sys.exit(f"Falló: {st}")
        time.sleep(8)

    try:
        res = api(resp_url, key)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            detail = json.loads(body)["detail"]
            if isinstance(detail, list):
                for d in detail:
                    print("ERROR", e.code, "-", d.get("type"), "-", d.get("msg"))
            else:
                print("ERROR", e.code, "-", detail)
        except Exception:
            print("ERROR", e.code, "-", body[:800])
        sys.exit(1)
    video_url = res["video"]["url"]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    urllib.request.urlretrieve(video_url, args.out)
    print(f"OK -> {args.out}")


if __name__ == "__main__":
    main()
