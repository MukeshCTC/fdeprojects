# fde-starter

Your development environment for the Generative AI FDE Program, checked by a script.
Python 3.12, git, VS Code, Docker and an NVIDIA API key, set up the same way on macOS,
Linux and Windows. When `make check` prints eight ✅, you are ready for every module.

```
hello_llm.py            one real LLM call; the key comes from .env
scripts/check_env.py    the ✅/❌ checklist (standard library only: runs before the venv exists)
requirements.txt        pinned dependencies
.env.example            copy to .env and paste your key; .env is git-ignored
docker-compose.yml      Qdrant, a vector database used in later modules
.vscode/                recommended extensions; the venv as the default interpreter
Makefile                setup · check · hello · up · ping · down · clean
MY_SETUP.md             your setup log (your first commit)
```

## Quick start (macOS and Linux)

```bash
git clone <this repo's URL or path> fde-starter && cd fde-starter
python3.12 scripts/check_env.py          # see what's missing
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                     # then paste your key into .env
python hello_llm.py
docker compose up -d && curl -s localhost:6333 && docker compose down
make check                               # 8/8 checks passed
```

## Quick start (Windows PowerShell)

```powershell
git clone <this repo's URL or path> fde-starter; cd fde-starter
py -3.12 scripts\check_env.py
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1               # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
Copy-Item .env.example .env              # then paste your key into .env
python hello_llm.py
docker compose up -d; curl.exe -s localhost:6333; docker compose down
python scripts\check_env.py
```

Prefer WSL 2 (Ubuntu) on Windows: then follow the Linux steps inside WSL, and Docker
Desktop's WSL integration gives you `docker` there too.

## Install the tools

| Tool | macOS | Windows | Linux (Ubuntu/Debian) |
|---|---|---|---|
| Python 3.12 | `brew install python@3.12` | `winget install Python.Python.3.12` (or python.org; tick "Add to PATH") | `sudo apt install python3.12 python3.12-venv` (older releases: deadsnakes PPA or pyenv) |
| git | `xcode-select --install` or `brew install git` | `winget install Git.Git` | `sudo apt install git` |
| VS Code | `brew install --cask visual-studio-code`, then Command Palette → "Shell Command: Install 'code' command in PATH" | `winget install Microsoft.VisualStudioCode` (adds `code` to PATH) | the .deb from code.visualstudio.com, or `sudo snap install code --classic` |
| Docker | Docker Desktop (Apple Silicon or Intel build); start it once and accept its terms | Docker Desktop with the WSL 2 backend | Docker Engine (`docs.docker.com/engine/install`), then `sudo usermod -aG docker $USER` and log in again |
| make (optional) | included with the Xcode command line tools | not needed: use the PowerShell commands above | `sudo apt install make` |

`uv` (from Astral) is a fast alternative to venv + pip: `uv venv && uv pip install -r requirements.txt`.
Use whichever your team uses; this repo works with both.

## Git, once per machine

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
ssh-keygen -t ed25519 -C "you@example.com"   # then add ~/.ssh/id_ed25519.pub (the PUBLIC key) to GitHub/GitLab
```

Your first commit: write one line in `MY_SETUP.md`, then

```bash
git switch -c my-setup
git add MY_SETUP.md && git commit -m "Log my environment setup"
```

`git status` never lists `.env` or `.venv/`: `.gitignore` keeps secrets and local files out
of the repo. Check with `git check-ignore -v .env`.

## API keys

1. Create a key in the provider's console (for NVIDIA: build.nvidia.com → your profile → API keys). Copy it once.
2. Paste it into `.env` (never into code, a notebook, a chat or a ticket).
3. `hello_llm.py` loads it with python-dotenv; `check_env.py` shows it masked (`nvapi-****…****`) and makes one live call.
4. If a key leaks (committed, pasted, screenshotted): revoke it in the console, create a new one, and update `.env`. Deleting the commit is not enough; the key is already out.

## VS Code

`code .` opens the folder. Install the recommended extensions when VS Code asks (or
`code --install-extension ms-python.python`). The interpreter is preset to `.venv`
(`.vscode/settings.json`); otherwise use Command Palette → "Python: Select Interpreter".
The integrated terminal (Ctrl+`) activates the venv for you.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python3 --version` says 3.9 (macOS) | That's the system Python. Use `python3.12`, or the venv's `python` once it's active. |
| `No module named venv` / `ensurepip` (Linux) | `sudo apt install python3.12-venv` |
| `Activate.ps1 cannot be loaded` (Windows) | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| pip: `SSL: CERTIFICATE_VERIFY_FAILED` | A corporate proxy re-signs TLS. Ask IT for the CA bundle; `pip config set global.cert /path/ca.pem`. |
| `code: command not found` | VS Code → Command Palette → "Shell Command: Install 'code' command in PATH" (macOS); reinstall with "Add to PATH" (Windows). |
| `Cannot connect to the Docker daemon` | Start Docker Desktop and wait for "Engine running"; Linux: `sudo systemctl start docker`. |
| `permission denied ... docker.sock` (Linux) | `sudo usermod -aG docker $USER`, then log out and in. |
| `port is already allocated` | Something else uses 6333: set `QDRANT_PORT=16333` in `.env` (or `QDRANT_PORT=16333 docker compose up -d`) and curl that port. |
| Check says HTTP 401 | The key is wrong or revoked: create a new one, paste it into `.env`. |
| Check says HTTP 429 | Rate limited: wait a minute and run again. |
| `no connection` on the live check | Proxy or firewall: set `HTTPS_PROXY`, or try another network. |
