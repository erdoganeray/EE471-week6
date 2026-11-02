# EE471 – Week 6 In-Class Exercise

EE 471 Modern Software Development Practices and Technologies, Izmir Institute of Technology.
Containerization with Docker and Cog.

| Path | Content |
|---|---|
| `EE471-week5/` | [Week 5 repository](https://github.com/erdoganeray/EE471-week5) as a Git submodule: the speech-studio website and the voice-activated calculator (unchanged) |
| `Task-1-Docker/` | Dockerfiles and a Compose file that containerize both Week 5 apps |
| `Task-2-Cog/` | Cat-kind classifier: Cog model container + website container |

## Setup

1. Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) (on Windows with the WSL 2 backend).
   For Task 2, install [Cog](https://github.com/replicate/cog#install) as well. Cog runs on Linux and macOS;
   on Windows install it inside WSL (Ubuntu) and turn on **Docker Desktop → Settings → Resources → WSL integration** for that distro:
   ```bash
   mkdir -p ~/.local/bin && curl -fsSL -o ~/.local/bin/cog https://github.com/replicate/cog/releases/latest/download/cog_$(uname -s)_$(uname -m) && chmod +x ~/.local/bin/cog
   ```
2. Clone the repository together with the submodules (Week 5 itself contains the Mini Project 1 submodule):
   ```bash
   git clone --recurse-submodules https://github.com/erdoganeray/EE471-week6.git
   ```
   If it was already cloned without them:
   ```bash
   git submodule update --init --recursive
   ```
3. Create your local secrets file from the template and fill in your Azure Speech key and region
   (how to get one: [Week 5 README](https://github.com/erdoganeray/EE471-week5#getting-an-azure-speech-key)):
   ```bash
   cp .env.example .env
   ```
   `.env` is listed in `.gitignore` and in the `.dockerignore` files, so it never gets pushed or copied into an image.
   Containers receive the values as environment variables when they start.

## Task 1: Containerized Week 5 apps

Build both images and start both containers:

```bash
docker compose -f Task-1-Docker/compose.yaml up --build
```

| App | URL |
|---|---|
| Speech-studio website | http://localhost:5000 |
| Voice-activated calculator | http://localhost:5001 |

Open them in Chrome or Edge and allow microphone access (browsers allow the microphone on `localhost` without HTTPS).
Stop with `Ctrl+C`, or `docker compose -f Task-1-Docker/compose.yaml down` when started with `-d`.

| File | Purpose |
|---|---|
| `speech-studio/Dockerfile` | Python 3.12 slim image + the native libraries the Azure Speech SDK needs (`libssl3`, `ca-certificates`, `libasound2`), served by Gunicorn |
| `voice-calculator/Dockerfile` | Python 3.12 slim image with the calculator and the Mini Project 1 `Calculator` class, served by Gunicorn |
| `*/Dockerfile.dockerignore` | Files left out of the build context (`.env`, `.git`, caches). Placed next to each Dockerfile because the context is the submodule |
| `compose.yaml` | Builds both images from the `EE471-week5` submodule, publishes the ports and passes `.env` to the containers |

<details>
<summary>Without Compose</summary>

```bash
docker build -f Task-1-Docker/speech-studio/Dockerfile -t speech-studio EE471-week5
```
```bash
docker run --rm -p 5000:5000 --env-file .env speech-studio
```
```bash
docker build -f Task-1-Docker/voice-calculator/Dockerfile -t voice-calculator EE471-week5
```
```bash
docker run --rm -p 5001:5000 --env-file .env voice-calculator
```
</details>

Useful commands:

```bash
docker compose -f Task-1-Docker/compose.yaml ps          # running containers and ports
docker compose -f Task-1-Docker/compose.yaml logs -f     # live request logs
docker exec -it task-1-docker-speech-studio-1 sh         # a shell inside the container
```

## Task 2: Cat-kind classifier with Cog

Upload a photo of a cat, press **Classify**, and see its kind. The model is the pre-trained ResNet-50
from [Cog's getting-started guide](https://github.com/replicate/cog/blob/main/docs/getting-started.md),
narrowed down to ImageNet's five domestic cat classes: tabby, tiger cat, Persian, Siamese and Egyptian cat.
Photos where these five classes get less than 20% together are reported as "not a cat", with what the model sees instead.

```
Browser ──(image file)──▶ web container (Flask, :8000) ──(JSON, data URI)──▶ model container (Cog, :5002)
```

The browser never calls the model directly: the website checks the file, converts it to the data URI that Cog expects,
and reaches the model by its Compose service name (`http://model:5000`).

### Run

1. Build the model image with Cog (in WSL on Windows). The first build downloads PyTorch and the ResNet-50 weights
   (about 100 MB, baked into the image so the container starts without downloading anything):
   ```bash
   cd Task-2-Cog/model
   cog build -t cat-classifier-model
   ```
2. Start the model and the website (from the repository root, in PowerShell or WSL):
   ```bash
   docker compose -f Task-2-Cog/compose.yaml up --build
   ```
   The website starts once the model reports `READY` (Compose health check).
3. Open http://localhost:8000.

To try the model alone, without the website or a running container:

```bash
cd Task-2-Cog/model
cog run -i image=@cat.jpg
```

| File | Purpose |
|---|---|
| `model/cog.yaml` | Cog's build recipe: Python version, `requirements.txt`, a `build.run` step that downloads the weights into the image, and the class that runs predictions (`run.py:Runner`). Cog turns it into a Docker image with an HTTP API |
| `model/run.py` | `setup()` loads ResNet-50 once when the container starts; `run()` classifies one image and logs it |
| `model/.dockerignore` | Keeps test images, caches and locally downloaded weights out of the build context |
| `web/app.py` | Flask website: `POST /api/classify` (form field `image`) forwards the photo to Cog, `GET /api/health` reports the model status |
| `web/Dockerfile` | Small Python image for the website (no PyTorch), served by Gunicorn |
| `compose.yaml` | Runs both containers, waits for the model's health check, and tells the website where the model is (`COG_URL`) |
| `test-images/` | Freely licensed photos to try: six cats of different kinds and five non-cats (dog, tiger, fox, car, guitar). Authors and licenses are in [`SOURCES.md`](Task-2-Cog/test-images/SOURCES.md) |

### Model API

| Method | URL | Body / response |
|---|---|---|
| `GET` | http://localhost:5002/health-check | `{"status": "READY", ...}` |
| `POST` | http://localhost:5002/predictions | `{"input": {"image": "<URL or data URI>"}}` → `{"status": "succeeded", "output": {...}}` |
| `GET` | http://localhost:5002/openapi.json | Input/output schema generated by Cog |

Example `output`:

```json
{
  "is_cat": true,
  "breed": "tiger cat",
  "confidence": 0.462,
  "cat_score": 0.995,
  "breeds": [{"label": "tiger cat", "probability": 0.462}, {"label": "Egyptian cat", "probability": 0.371}, "..."],
  "top_predictions": [{"label": "tiger cat", "probability": 0.460}, "..."]
}
```

`confidence` and `breeds` are relative to the five cat classes, `cat_score` is how much of the whole prediction went to cats.

### Testing with Postman

Cog only accepts JSON, with files inside as data URIs. [`postman/make_request.py`](Task-2-Cog/postman/make_request.py)
turns an image into that JSON:

```bash
python Task-2-Cog/postman/make_request.py cat.jpg
```

Import [`postman/cat-classifier.postman_collection.json`](Task-2-Cog/postman/cat-classifier.postman_collection.json) into Postman,
open **Classify a cat (JSON body file)**, choose the generated `cat.json` under **Body → binary**, and press **Send**.
The collection also has a health check and a request that classifies an image from a URL.

### Prediction logs inside the container

Every prediction is written to the container's output and to `/tmp/predictions.log` inside it:

```bash
docker exec -it task-2-cog-model-1 tail -f /tmp/predictions.log   # from inside the model container
docker compose -f Task-2-Cog/compose.yaml logs -f                 # both containers
```

```
2026-11-02 11:37:10,712 INFO size=1795x2397 cat_score=0.995 breed=tiger cat confidence=0.462 top1=tiger cat
```
