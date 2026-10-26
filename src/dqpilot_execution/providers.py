"""Provider-independent, content-addressed inference with local-only endpoints."""

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from dqpilot.common import digest, now, sha


def process_tree_rss(pid):
    total = 0
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                total += int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    try:
        children = Path(f"/proc/{pid}/task/{pid}/children").read_text().split()
        for child in children:
            total += process_tree_rss(int(child))
    except (OSError, ValueError):
        pass
    return total


class LocalProvider:
    def __init__(
        self,
        root,
        backend="llamacpp",
        endpoint="http://127.0.0.1:11435",
        transport=None,
        condition="frozen_original",
    ):
        u = urlparse(endpoint)
        if u.scheme != "http" or u.hostname != "127.0.0.1" or u.username or u.password or u.path:
            raise ValueError("A literal loopback-only local endpoint is required")
        if backend not in {"llamacpp", "ollama"}:
            raise ValueError("Unsupported local backend")
        self.root, self.backend, self.endpoint = Path(root), backend, endpoint
        self.transport = transport
        self.condition = condition
        if condition not in {"frozen_original", "gx_syntax_guided_v1", "published_schema_v1"}:
            raise ValueError("Explicit frozen condition required")
        self.config = json.loads((self.root / "results/execution/local_model.json").read_text())
        name = "inference.sqlite" if condition == "frozen_original" else "inference_" + condition + ".sqlite"
        self.db = sqlite3.connect(self.root / "data/cache/execution" / name)
        self.db.execute("""CREATE TABLE IF NOT EXISTS calls(
          hash TEXT PRIMARY KEY,status TEXT,started TEXT,request TEXT,response TEXT,provenance TEXT)""")
        self.db.commit()

    def generate(self, prompt, seed):
        c = self.config
        if len(prompt.encode()) > 16000:
            raise ValueError("Frozen prompt byte ceiling exceeded")
        settings = {
            "temperature": 0,
            "seed": seed,
            "top_p": 1,
            "repeat_penalty": 1,
            "max_tokens": 2048,
            "context_tokens": 8192,
            "cpu_threads": 4,
        }
        key = digest(
            {
                "model_sha256": c["weights_sha256"],
                "runtime": c["runtime_commit"],
                "backend": self.backend,
                "prompt": prompt,
                "settings": settings,
            }
        )
        cached = self.db.execute(
            "SELECT status,response,provenance FROM calls WHERE hash=?", (key,)
        ).fetchone()
        if cached:
            if cached[0] != "COMPLETE":
                raise RuntimeError("Preserved incomplete attempt: " + cached[0])
            return json.loads(cached[1]), json.loads(cached[2]), True
        if self.backend == "llamacpp":
            route = "/v1/chat/completions"
            payload = {
                "model": c["model_alias"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "seed": seed,
                "top_p": 1,
                "repeat_penalty": 1,
                "max_tokens": 2048,
                "stream": False,
                "response_format": {"type": "json_object"},
                "timings": True,
            }
        else:
            route = "/api/generate"
            payload = {
                "model": c["model_alias"],
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "keep_alive": "30m",
                "options": {
                    "seed": seed,
                    "temperature": 0,
                    "top_p": 1,
                    "repeat_penalty": 1,
                    "num_ctx": 8192,
                    "num_predict": 2048,
                    "num_thread": 4,
                    "num_gpu": 0,
                },
            }
        self.db.execute(
            "INSERT INTO calls VALUES(?,?,?,?,?,?)", (key, "STARTED", now(), json.dumps(payload), None, None)
        )
        self.db.commit()
        stop, peaks = threading.Event(), []

        def monitor():
            pid_file = self.root / "data/cache/execution/server.pid"
            pid = int(pid_file.read_text()) if pid_file.exists() else c.get("server_pid", 0)
            while not stop.is_set():
                peaks.append(process_tree_rss(pid))
                stop.wait(0.5)

        watcher = threading.Thread(target=monitor, daemon=True)
        watcher.start()
        began = time.perf_counter()
        try:
            with httpx.Client(
                timeout=600, transport=self.transport, follow_redirects=False, trust_env=False
            ) as client:
                key_file = self.root / "data/cache/execution/local_api.key"
                headers = (
                    {"Authorization": "Bearer " + key_file.read_text().strip()} if key_file.exists() else {}
                )
                result = client.post(self.endpoint + route, json=payload, headers=headers)
                result.raise_for_status()
                raw = result.json()
            if self.backend == "llamacpp":
                choice = raw["choices"][0]
                text, finish = choice["message"]["content"], choice["finish_reason"]
                usage, timing = raw.get("usage"), raw.get("timings")
            else:
                text, finish = raw["response"], raw.get("done_reason", "stop")
                usage = {
                    "prompt_tokens": raw.get("prompt_eval_count"),
                    "completion_tokens": raw.get("eval_count"),
                }
                timing = {
                    k: raw.get(k)
                    for k in ["load_duration", "prompt_eval_duration", "eval_duration", "total_duration"]
                }
            provenance = {
                "provider": self.backend,
                "experimental_condition": self.condition,
                "model": c["base_model"],
                "model_alias": c["model_alias"],
                "weights_revision": c["weights_revision"],
                "weights_sha256": c["weights_sha256"],
                "quantization": c["quantization"],
                "runtime_commit": c["runtime_commit"],
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "request_sha256": digest(payload),
                "response_canonical_sha256": digest(raw),
                "settings": settings,
                "usage": usage,
                "timings": timing,
                "runtime_seconds": time.perf_counter() - began,
                "peak_server_tree_RSS_bytes": max(peaks, default=0),
                "finish_reason": finish,
                "origin": "EXPERIMENTAL_MODEL_RESPONSE",
                "paid_calls": 0,
            }
            envelope = {
                "modelVersion": c["weights_sha256"],
                "usageMetadata": usage,
                "candidates": [
                    {
                        "finishReason": "STOP" if finish in {"stop", "eos"} else "MAX_TOKENS",
                        "content": {"parts": [{"text": text}]},
                    }
                ],
            }
            # Original response bytes/text stay in ignored storage before parsing/evaluation.
            path = self.root / "data/cache/execution/responses" / (key + ".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(result.content)
            provenance["response_wire_sha256"] = sha(path)
            self.db.execute(
                "UPDATE calls SET status=?,response=?,provenance=? WHERE hash=?",
                ("COMPLETE", json.dumps(envelope), json.dumps(provenance), key),
            )
            self.db.commit()
            return envelope, provenance, False
        except Exception as e:
            self.db.execute("UPDATE calls SET status=? WHERE hash=?", ("FAILED_" + type(e).__name__, key))
            self.db.commit()
            raise
        finally:
            stop.set()
            watcher.join(2)

    def close(self):
        self.db.close()


class GeminiProvider:
    """Reuse the already tested free-project gate; never infer billing entitlement."""

    def __init__(self, root):
        import yaml
        from dqpilot_free.gemini import GeminiFree

        self.root = Path(root)
        c = yaml.safe_load((self.root / "config/free_gemini/pilot.yaml").read_text())
        self.original = GeminiFree(c, self.root / "data/cache/execution/gemini.sqlite")
        self.metadata = self.original.model_access()

    def generate(self, prompt, seed):
        result, cached = self.original.generate(prompt, seed, source_approved=True)
        return (
            result,
            {
                "provider": "Gemini_free_only",
                "model": result.get("modelVersion"),
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "response_canonical_sha256": digest(result),
                "usage": result.get("usageMetadata"),
                "origin": "EXPERIMENTAL_MODEL_RESPONSE",
                "paid_calls": 0,
            },
            cached,
        )

    def close(self):
        self.original.close()
