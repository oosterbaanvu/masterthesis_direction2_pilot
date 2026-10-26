"""Recreate the measured CPU runtime from pinned, checksum-verified public artifacts.

No inference, billing, root installation, home-directory changes, or experiment overwrite.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[2]
cache = root / "data/cache/execution"
parser = argparse.ArgumentParser()
parser.add_argument("--verify-only", action="store_true")
args = parser.parse_args()
model = json.loads((root / "results/execution/local_model.json").read_text())
source = json.loads((root / "results/execution/llama_source.json").read_text())
items = [
    {
        "name": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/"
        + model["weights_revision"]
        + "/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "sha256": model["weights_sha256"],
    },
    {
        "name": "llama-source.tar.gz",
        "url": "https://codeload.github.com/ggml-org/llama.cpp/tar.gz/" + source["commit"],
        "sha256": source["archive_sha256"],
    },
]


def checksum(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


for item in items:
    path = cache / "downloads" / item["name"]
    # Reuse the original acquisition filename when present.
    if item["name"] == "llama-source.tar.gz":
        originals = list((cache / "downloads").glob("llama*.tar.gz")) + [cache / "llama/source.tar.gz"]
        originals = [p for p in originals if p.exists()]
        if originals:
            path = originals[0]
    if not path.exists():
        if args.verify_only:
            raise FileNotFoundError(path)
        required = 8 * 1024**3 + (4683073536 if item["name"].endswith("gguf") else 40000000)
        if shutil.disk_usage(root).free < required:
            raise RuntimeError("Preserve 8 GiB disk headroom before artifact acquisition")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        with urlopen(
            Request(item["url"], headers={"User-Agent": "dqpilot-reproduction/1"}), timeout=60
        ) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output, 4 * 1024 * 1024)
        if checksum(temporary) != item["sha256"]:
            raise ValueError("Downloaded artifact checksum mismatch")
        temporary.replace(path)
    if checksum(path) != item["sha256"]:
        raise ValueError("Cached artifact checksum mismatch: " + path.name)
    item["path"] = path
    print("Verified", path.name, flush=True)

binary = cache / "llama/build/bin/llama-server"
if args.verify_only:
    if not binary.exists():
        raise FileNotFoundError(binary)
    print("Runtime present; original binary match:", checksum(binary) == model["runtime_binary_sha256"])
else:
    if binary.exists() and checksum(binary) == model["runtime_binary_sha256"]:
        print("Original measured CPU binary verified; no rebuild needed.")
        raise SystemExit(0)
    source_root = cache / "llama/source"
    if not (source_root / "CMakeLists.txt").exists():
        source_root.mkdir(parents=True, exist_ok=True)
        with tarfile.open(items[1]["path"]) as archive:
            prefix = archive.getmembers()[0].name.split("/")[0] + "/"
            members = []
            for member in archive.getmembers():
                if not member.name.startswith(prefix):
                    continue
                member.name = member.name[len(prefix) :]
                if member.name:
                    members.append(member)
            archive.extractall(source_root, members=members, filter="data")
    build = cache / "llama/build"
    environment = os.environ.copy()
    environment.update(
        UV_CACHE_DIR="/workspace/.cache/uv",
        UV_TOOL_DIR="/workspace/.cache/uv/tools",
        UV_TOOL_BIN_DIR="/workspace/.cache/uv/bin",
    )
    cmake = ["uvx", "--from", "cmake==4.1.2", "cmake"]
    subprocess.run(
        cmake
        + [
            "-S",
            str(source_root),
            "-B",
            str(build),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DGGML_NATIVE=ON",
            "-DGGML_CUDA=OFF",
            "-DLLAMA_CURL=OFF",
            "-DLLAMA_BUILD_TESTS=OFF",
            "-DLLAMA_BUILD_SERVER=ON",
        ],
        check=True,
        env=environment,
    )
    subprocess.run(
        cmake + ["--build", str(build), "--target", "llama-server", "llama-bench", "-j4"],
        check=True,
        env=environment,
    )
    print(
        "CPU runtime built. Host-specific binary differences must be recorded; source/model hashes stay pinned."
    )
