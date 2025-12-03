# Testing chutes-inspecto.so

```bash
# Exit code 0 (success)
docker pull parachutes/base-python:3.12
docker run --rm --entrypoint "" parachutes/base-python:3.12 bash -c 'pip install chutes --upgrade >/dev/null 2>&1 && chutes run does_not_exist:chute --generate-inspecto-hash; echo EXIT:$?'
```

```bash
# Exit code 139 (SIGSEGV - segmentation fault)
docker pull elbios/xtts-whisper:latest
docker run --rm --entrypoint "" elbios/xtts-whisper:latest bash -c 'pip install chutes --upgrade >/dev/null 2>&1 && chutes run does_not_exist:chute --generate-inspecto-hash; echo EXIT:$?'
```

```bash
# Exit code 139 (SIGSEGV - segmentation fault)
chutes build deploy_example_xtts_whisper:chute --wait --local
docker run --rm --entrypoint "" xtts-whisper:tts-stt-v0.1.1 bash -c 'pip install chutes --upgrade >/dev/null 2>&1 && chutes run does_not_exist:chute --generate-inspecto-hash; echo EXIT:$?'
```

```bash
# Exit code 0 (success)
docker pull nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04
docker run --rm --entrypoint "" nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04 bash -c 'export DEBIAN_FRONTEND=noninteractive NEEDRESTART_SUSPEND=y && apt update && apt -y upgrade && apt autoclean -y && apt -y autoremove && echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" > /etc/apt/sources.list.d/deadsnakes.list && (apt update || true) && apt -y install gpg && gpg --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776 && gpg --export F23C5A6CF475977595C89F51BA6932366A755776 > /etc/apt/trusted.gpg.d/deadsnakes.gpg && apt update && apt -y install python3.12-full python3.12-dev && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && update-alternatives --set python3 /usr/bin/python3.12 && rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED && ln -sf $(which python3.12) /usr/bin/python && python3.12 -m ensurepip && apt update && apt -y install libclblast-dev clinfo ocl-icd-libopencl1 opencl-headers ocl-icd-opencl-dev libudev-dev libopenmpi-dev vim git git-lfs cmake automake pkg-config gcc g++ openssh-server curl wget jq && mkdir -p /etc/OpenCL/vendors/ && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd && useradd chutes && mkdir -p /home/chutes /app && chown -R chutes:chutes /home/chutes /app && usermod -aG root chutes && chmod g+wrx /usr/local/lib/python3.12/dist-packages /usr/local/bin /usr/local/lib /usr/local/share /usr/local/share/man && python -m pip install uv && mkdir -p /home/chutes/.local/bin && printf "#!/bin/bash\nexec uv pip \"\$@\"\n" > /home/chutes/.local/bin/pip && chmod 755 /home/chutes/.local/bin/pip && chown -R chutes:chutes /home/chutes/.local && export PATH=/home/chutes/.local/bin:$PATH UV_SYSTEM_PYTHON=1 UV_CACHE_DIR=/home/chutes/.cache/uv && uv python pin 3.12 && rm -rf /home/chutes/.cache && cd /app && uv pip install chutes --upgrade && chutes run does_not_exist:chute --generate-inspecto-hash && echo EXIT:$?'
```

```bash
# Exit code 4503 Segmentation fault (core dumped)
docker pull elbios/xtts-whisper:latest
docker run --rm --entrypoint "" elbios/xtts-whisper:latest bash -c 'export DEBIAN_FRONTEND=noninteractive NEEDRESTART_SUSPEND=y && apt update && apt -y upgrade && apt autoclean -y && apt -y autoremove && echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" > /etc/apt/sources.list.d/deadsnakes.list && (apt update || true) && apt -y install gpg && gpg --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776 && gpg --export F23C5A6CF475977595C89F51BA6932366A755776 > /etc/apt/trusted.gpg.d/deadsnakes.gpg && apt update && apt -y install python3.12-full python3.12-dev && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && update-alternatives --set python3 /usr/bin/python3.12 && rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED && ln -sf $(which python3.12) /usr/bin/python && python3.12 -m ensurepip && apt update && apt -y install libclblast-dev clinfo ocl-icd-libopencl1 opencl-headers ocl-icd-opencl-dev libudev-dev libopenmpi-dev vim git git-lfs cmake automake pkg-config gcc g++ openssh-server curl wget jq && mkdir -p /etc/OpenCL/vendors/ && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd && useradd chutes && mkdir -p /home/chutes /app && chown -R chutes:chutes /home/chutes /app && usermod -aG root chutes && chmod g+wrx /usr/local/lib/python3.12/dist-packages /usr/local/bin /usr/local/lib /usr/local/share /usr/local/share/man && python -m pip install uv && mkdir -p /home/chutes/.local/bin && printf "#!/bin/bash\nexec uv pip \"\$@\"\n" > /home/chutes/.local/bin/pip && chmod 755 /home/chutes/.local/bin/pip && chown -R chutes:chutes /home/chutes/.local && export PATH=/home/chutes/.local/bin:$PATH UV_SYSTEM_PYTHON=1 UV_CACHE_DIR=/home/chutes/.cache/uv && uv python pin 3.12 && rm -rf /home/chutes/.cache && cd /app && uv pip install chutes --upgrade && chutes run does_not_exist:chute --generate-inspecto-hash && echo EXIT:$?'
```
