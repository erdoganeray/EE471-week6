"""Cat-kind classifier website: takes an uploaded photo and asks the Cog model container to classify it."""
import base64
import logging
import os

import requests
from flask import Flask, jsonify, render_template, request

# Address of the Cog model. In Docker Compose this is http://model:5000 (the service name),
# when the website runs directly on the computer it is the published port.
COG_URL = os.getenv("COG_URL", "http://localhost:5002").rstrip("/")
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
PREDICTION_TIMEOUT = 60  # seconds; a CPU prediction takes about 1 s

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_BYTES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cat-web")


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/classify")
def classify():
    image = request.files.get("image")

    if image is None or not image.filename:
        return jsonify(error="Please choose a photo of a cat."), 400
    if image.mimetype not in ALLOWED_TYPES:
        return jsonify(error="Please use a JPEG, PNG, WebP, GIF or BMP image."), 400

    data = image.read()
    if not data:
        return jsonify(error="The file is empty."), 400

    # Cog accepts files inside JSON as data URIs: data:<type>;base64,<content>
    data_uri = f"data:{image.mimetype};base64,{base64.b64encode(data).decode()}"

    try:
        response = requests.post(
            f"{COG_URL}/predictions",
            json={"input": {"image": data_uri}},
            timeout=PREDICTION_TIMEOUT,
        )
        prediction = response.json()
    except (requests.RequestException, ValueError):
        log.exception("Model service at %s is unreachable", COG_URL)
        return jsonify(error="The model service is not reachable. Is the Cog container running?"), 502

    if response.status_code != 200 or prediction.get("status") != "succeeded":
        log.warning("Prediction failed: %s", prediction.get("error") or prediction)
        # The model answered, so the file is the problem (e.g. a .png that isn't really an image)
        return jsonify(error="The model could not read this image. Is it a valid image file?"), 422

    output = prediction["output"]
    log.info("%s (%d KB) -> %s, %.0f ms", image.filename, len(data) // 1024,
             output["breed"] or "not a cat", prediction.get("metrics", {}).get("predict_time", 0) * 1000)
    return jsonify(output)


@app.get("/api/health")
def health():
    """Tells the page whether the model container is ready (Cog reports STARTING while setup() runs)."""
    try:
        status = requests.get(f"{COG_URL}/health-check", timeout=3).json().get("status", "UNKNOWN")
    except (requests.RequestException, ValueError):
        status = "UNREACHABLE"
    return jsonify(model=status)


@app.errorhandler(413)
def file_too_large(_):
    return jsonify(error=f"The image is too large (max {MAX_IMAGE_BYTES // (1024 * 1024)} MB)."), 413


if __name__ == "__main__":
    app.run(debug=True)
