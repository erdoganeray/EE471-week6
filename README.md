# EE471 – Week 6 In-Class Exercise

EE 471 Modern Software Development Practices and Technologies, Izmir Institute of Technology.
Containerization with Docker and Cog.

| Path | Content |
|---|---|
| `EE471-week5/` | [Week 5 repository](https://github.com/erdoganeray/EE471-week5) as a Git submodule: the speech-studio website and the voice-activated calculator (unchanged) |
| `Task-1-Docker/` | Dockerfiles and a Compose file that containerize both Week 5 apps |
| `Task-2-Cog/` | Cat-kind classifier: Cog model + website (in progress) |

## Setup

1. Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) (on Windows with the WSL 2 backend).
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
