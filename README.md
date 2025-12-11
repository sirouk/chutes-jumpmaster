# Chutes Wrappers

Toolkit for wrapping upstream Docker images so they can be deployed, monitored, and iterated on via [Chutes.ai](https://chutes.ai). This repo mirrors the SkyrimNet chute tooling but keeps everything generic so you can reuse the same workflow for any service.

---

## Quick Start

```bash
# 1. Setup environment (creates .venv, installs deps, registers with Chutes)
./setup.sh

# 2. Activate and use deploy.sh for everything else
source .venv/bin/activate
./deploy.sh
```

---

## Architecture & Methodology

**Strategy:** Keep the vendor image intact and inject the Chutes runtime so the exact same binaries continue to run. Only use the metadata-rebuild path (replaying steps onto the `parachutes/python` base) when you explicitly want a fresh foundation—for example, to audit each layer or to publish a clean-room replica. Even if the upstream container uses Conda or custom CUDA stacks, we still prefer to wrap *that* image so it behaves identically once deployed.

### Tooling
- **Wrapper SDK (`tools/chute_wrappers.py`):** Injects system Python, the `chutes` user, OpenCL libs, and helper scripts into any base image. Handles route registration, startup waits, and health checks.
- **Auto-Discovery (`deploy.sh --discover` / `tools/discover_routes.py`):** Boots the upstream image locally, probes common OpenAPI endpoints, and writes `deploy_*.routes.json` so passthrough cords can be generated automatically.
- **Image Generator (`tools/create_chute_from_image.py`):** Replays an existing Docker image’s metadata on top of the Chutes base (`deploy_*_auto.py`), giving you a reproducible python-first version that still launches the original entrypoint.

### Platform Context
Chutes behaves like a less restrictive, GPU-aware AWS Lambda. Containers can stay warm, keep local caches, and expose arbitrary HTTP routes. The current router requires JSON payloads for billing and quota enforcement, so legacy `multipart/form-data` uploads (typical for `xtts` and `whisper.cpp`) must be converted to JSON with base64 audio.

- **Workaround Today:** Update clients (or add a thin proxy) to wrap binary blobs in JSON before hitting the chute.
- **Future Direction:** Images can return JSON-wrapped audio responses as well, opening the door to multi-part emulation in the SDK later.

---

## Workflow

### 1. Setup (`./setup.sh`)
Interactive wizard that:
- Installs `uv` and creates `.venv` (Python 3.11)
- Installs the `chutes` CLI and supporting deps
- Helps you register / configure wallets in `~/.chutes/config.ini`

### 2. Deploy (`./deploy.sh`)
Menu overview (press Enter for defaults when prompted):

| Option | Description |
|--------|-------------|
| **1** Account info | Show username + payment address from config |
| **2** List images | Built chute images |
| **3** List chutes | Deployed chutes |
| **4** Build chute from existing `deploy_*.py` (wraps `CHUTE_BASE_IMAGE`) |
| **5** Create `deploy_*_auto.py` (replays image on Chutes base) |
| **6** Run in Docker (GPU) | Sanity-check wrapped services |
| **7** Run dev mode | Host-run for Python chutes |
| **8** Deploy chute | Upload + schedule on Chutes.ai |
| **9** Warmup once | Ping the chute so it spins up |
| **10** Keep warm loop | Repeated warmup |
| **11** Chute status | Calls `chutes chutes get` |
| **12** Instance logs | Streams logs for active instances |
| **13** Delete chute | Interactive safety checks |
| **14** Delete image | Remove local/remote image |

**CLI Examples**
```bash
./deploy.sh --discover deploy_xtts_whisper
./deploy.sh --build deploy_xtts_whisper --local
./deploy.sh --deploy deploy_xtts_whisper --accept-fee
```

### 3. Route Discovery

```bash
./deploy.sh --discover deploy_myservice
```
1. Starts the base image in Docker with GPU access
2. Waits for startup
3. Probes `/openapi.json`, `/docs.json`, `/docs/openapi.json`, `/swagger.json`
4. Writes `deploy_myservice.routes.json`

If no manifest exists when you choose “Build chute,” the script now defaults the discovery prompt to **Yes** to avoid deploying an image with no cords.

---

## Deploy Script Structure

```python
from tools.chute_wrappers import build_wrapper_image, load_route_manifest, register_passthrough_routes

CHUTE_NAME = "xtts-whisper"
CHUTE_TAG = "tts-stt-v0.1.16"
CHUTE_BASE_IMAGE = "elbios/xtts-whisper:latest"
SERVICE_PORTS = [8020, 8080]
CHUTE_STATIC_ROUTES = [{"port": 8080, "method": "POST", "path": "/inference"}]

image = build_wrapper_image(USERNAME, CHUTE_NAME, CHUTE_TAG, CHUTE_BASE_IMAGE, env=CHUTE_ENV)

chute = Chute(
    username=USERNAME,
    name=CHUTE_NAME,
    image=image,
    node_selector=NodeSelector(gpu_count=1, min_vram_gb_per_gpu=16),
)

register_passthrough_routes(
    chute,
    load_route_manifest(static_routes=CHUTE_STATIC_ROUTES),
    SERVICE_PORTS[0],
)
```

---

## Troubleshooting Cheat Sheet

| Issue | Fix |
|-------|-----|
| Multipart calls return 400 | Convert to JSON + base64 payload, or add a proxy that does it |
| No routes discovered | Add `CHUTE_STATIC_ROUTES` or rerun discovery with longer delays |
| Build segfaults | Ensure `build_wrapper_image` injects system Python; Conda-only bases fail `chutes-inspecto` |
| Remote build rejected | Requires ≥ $50 balance; use `--local` during development |
| Chute never warms | Use menu option 10 (keep warm loop) and watch instance logs |

---

## Repository Layout

```
chutes-wrappers/
├── setup.sh                     # Environment setup (venv, deps, registration)
├── deploy.sh                    # Main CLI (interactive + flags)
├── requirements.txt             # Python deps
├── deploy_example_*.py          # Reference modules
├── tools/
│   ├── chute_wrappers.py        # Image builder, route helpers
│   ├── discover_routes.py       # OpenAPI probing
│   ├── create_chute_from_image.py  # Metadata → deploy_auto generator
│   └── instance_logs.py         # Log streaming utilities
├── DOCKER_TROUBLESHOOTING.md    # Notes on Python/inspecto issues
└── README.md
```

---

## Links
- [Chutes Documentation](https://chutes.ai/docs)
- [SDK Image Reference](https://chutes.ai/docs/sdk-reference/image)
- [Registration Token](https://rtok.chutes.ai/users/registration_token)

Everything in this repo stays in lock-step with the SkyrimNet chute bundle, so keeping these files synced guarantees the “wrapper” tooling behaves the same in both places. Let us know if you need the docs expanded to cover additional workflows (gRPC, websocket passthrough, etc.).
