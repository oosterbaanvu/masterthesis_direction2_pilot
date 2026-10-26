"""Strictly validated, bounded subprocess execution; never unrestricted model Python."""

import json
import resource
import sys

from dqpilot_execution.safety import validate
from dqpilot_free.worker import execute

resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
data = json.load(sys.stdin)
good = []
output = []
for candidate in data["candidates"]:
    try:
        validate(candidate["gx_code"], data["columns"])
        good.append(candidate)
    except Exception as e:
        output.append(
            {
                "id": candidate["id"],
                "technical_pass": False,
                "status": "SAFETY_OR_COMPATIBILITY_REJECTED",
                "reason": str(e) if isinstance(e, ValueError) else type(e).__name__,
                "semantic_validity": "NOT_ADJUDICATED",
            }
        )
if good:
    output.extend(execute(dict(data, candidates=good)))
print(json.dumps(output, allow_nan=False))
