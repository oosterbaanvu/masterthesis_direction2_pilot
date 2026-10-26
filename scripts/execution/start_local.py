"""Start or reuse the authenticated loopback CPU server; perform a functional readiness check."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import time

import httpx

root = Path(__file__).resolve().parents[2]
cache = root / "data/cache/execution"
configuration = json.loads((root / "results/execution/local_model.json").read_text())
key = cache / "local_api.key"
cache.mkdir(parents=True, exist_ok=True)
if not key.exists():
    fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(secrets.token_hex(32))
headers = {"Authorization": "Bearer " + key.read_text().strip()}
endpoint = "http://127.0.0.1:11435"
with httpx.Client(trust_env=False, timeout=5, headers=headers) as client:
    try:
        response = client.get(endpoint + "/v1/models")
        response.raise_for_status()
    except httpx.ConnectError:
        binary = cache / "llama/build/bin/llama-server"
        weights = cache / "downloads/qwen2.5-coder-7b-instruct-q4_k_m.gguf"
        if not binary.exists() or not weights.exists():
            raise RuntimeError("Run scripts/execution/acquire_local.py first") from None
        command = [
            str(binary),
            "-m",
            str(weights),
            "--host",
            "127.0.0.1",
            "--port",
            "11435",
            "-a",
            configuration["model_alias"],
            "-c",
            "8192",
            "-np",
            "1",
            "-t",
            "4",
            "-tb",
            "4",
            "-ngl",
            "0",
            "--jinja",
            "--no-ui",
            "--metrics",
            "--cors-origins",
            endpoint,
            "--api-key-file",
            str(key),
        ]
        with (cache / "llama/server.log").open("a") as log:
            server = subprocess.Popen(
                command, cwd=root, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
            )
        (cache / "server.pid").write_text(str(server.pid))
        for _ in range(50):
            if server.poll() is not None:
                raise RuntimeError("Local server exited; inspect ignored llama/server.log")
            try:
                response = client.get(endpoint + "/v1/models")
                if response.status_code == 200:
                    break
            except httpx.ConnectError:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError("Server readiness timed out; process preserved for diagnosis")
    response.raise_for_status()
    aliases = [item["id"] for item in response.json()["data"]]
    if configuration["model_alias"] not in aliases:
        raise RuntimeError("Unexpected local model alias")
    # Tokenization exercises the loaded model without adding a generation request.
    tokens = client.post(endpoint + "/tokenize", json={"content": "data quality"})
    tokens.raise_for_status()
    if not tokens.json()["tokens"]:
        raise RuntimeError("Functional tokenizer check failed")
print("Authenticated local model API and tokenization ready; no inference or paid requests made.")
