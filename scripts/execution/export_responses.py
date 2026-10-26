"""Export actual new public-metadata model outputs, never raw datasets or authentication headers."""

import json
import sqlite3
from pathlib import Path

from dqpilot.common import save, sha, digest

root = Path(__file__).resolve().parents[2]
files = []
for db in sorted((root / "data/cache/execution").glob("inference*.sqlite")):
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT hash,request,provenance FROM calls WHERE status='COMPLETE'").fetchall()
    for key, request, provenance in rows:
        wire = root / "data/cache/execution/responses" / f"{key}.json"
        metadata = json.loads(provenance)
        payload = json.loads(request)
        assert digest(payload) == metadata["request_sha256"]
        request_output = root / "results/execution/raw_model_requests" / f"{key}.json"
        if request_output.exists() and json.loads(request_output.read_text()) != payload:
            raise ValueError("Saved model request changed")
        if not request_output.exists():
            save(request_output, payload)
        assert sha(wire) == metadata["response_wire_sha256"]
        output = root / "results/execution/raw_model_responses" / f"{key}.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and output.read_bytes() != wire.read_bytes():
            raise ValueError("Saved model response changed")
        if not output.exists():
            output.write_bytes(wire.read_bytes())
        files.append(
            {
                "request_cache_key": key,
                "response_wire_sha256": sha(output),
                "path": output.relative_to(root).as_posix(),
                "request_path": request_output.relative_to(root).as_posix(),
                "request_canonical_sha256": digest(payload),
                "provenance": metadata,
            }
        )
save(
    root / "results/execution/response_inventory.json",
    {
        "actual_completed_generation_requests": len(files),
        "files": files,
        "model_input_scope": "Public source metadata and self-authored examples only; no source records transmitted",
        "responses_are_actual_new_experiments": True,
        "raw_datasets_or_weights_redistributed": False,
    },
)
print("Actual responses exported:", len(files))
