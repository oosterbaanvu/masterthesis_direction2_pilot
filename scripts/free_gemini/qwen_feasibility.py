"""Measured host limits and content-pinned Qwen sizing; no invented throughput."""
import json
import os
import shutil
from pathlib import Path

from dqpilot.common import save

root = Path(__file__).resolve().parents[2]
research = root / 'data/cache/free_gemini/research'
metadata = json.loads((research / 'qwen_gguf_metadata.json').read_text())
tree = json.loads((research / 'qwen_gguf_tree.json').read_text())
model_config = json.loads((research / 'qwen_model_config.json').read_text())
file = next(x for x in tree if x['path'] == 'Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf')
memory_limit = int(Path('/sys/fs/cgroup/memory.max').read_text().strip())
quota, period = Path('/sys/fs/cgroup/cpu.max').read_text().split()
kv = {}
for context in [4096, 8192, 16384, 262144]:
    kv[context] = 2 * model_config['num_hidden_layers'] * model_config['num_key_value_heads'] * model_config['head_dim'] * 2 * context
result = {'status': 'CPU_GGUF_POTENTIALLY_FITS_NOT_BENCHMARKED',
    'cpu_affinity_count': len(os.sched_getaffinity(0)), 'cpu_quota_equivalent_vcpus': int(quota) / int(period),
    'memory_limit_bytes': memory_limit, 'disk_free_bytes': shutil.disk_usage(root).free,
    'nvidia_device_present': Path('/dev/nvidia0').exists(),
    'installed_runtimes': {k: shutil.which(k) for k in ['ollama', 'llama-cli', 'llama-bench', 'cmake', 'g++']},
    'paper_exact_AWQ_stack': 'NOT_AVAILABLE_NO_CUDA_DEVICE',
    'alternative_quantization': 'GGUF Q4_K_M, CPU llama.cpp; differs from paper AWQ',
    'weights_repository': metadata['id'], 'weights_revision': metadata['sha'],
    'weights_file': file['path'], 'weights_bytes': file['size'], 'weights_sha256_publisher_LFS': file['lfs']['oid'],
    'licence': metadata.get('cardData', {}).get('license'),
    'llama_cpp_reference_commit': '620d2225cc436ab0b001e3200e590e3b286ef9ab',
    'qwen3moe_architecture_in_pinned_runtime_source': 'qwen3moe' in (research / 'llama_architecture.txt').read_text(),
    'fp16_KV_cache_bytes_single_sequence_estimate': kv,
    'sizing_not_measured_runtime_memory': True,
    'weights_plus_8192_KV_plus_4GiB_planning_overhead_fits_memory': file['size'] + kv[8192] + 4 * 1024**3 < memory_limit,
    'weights_plus_1GB_runtime_and_8GB_reserve_fits_disk': file['size'] + 1000000000 + 8000000000 < shutil.disk_usage(root).free,
    'generation_tokens_per_second': None, 'model_loaded': False, 'actual_model_generations': 0,
    'download_probe': json.loads((root / 'results/free_gemini/qwen_download_probe.json').read_text()),
    'recommended_if_runtime_and_download_are_available': {'context_tokens': 8192, 'cpu_threads': 4, 'gpu_layers': 0,
        'max_initial_generation_tokens': 256, 'benchmark_before_full_pilot': True}}
save(root / 'results/free_gemini/qwen_feasibility.json', result)
print(json.dumps({k: result[k] for k in ['status', 'cpu_quota_equivalent_vcpus', 'memory_limit_bytes',
    'weights_bytes', 'weights_plus_8192_KV_plus_4GiB_planning_overhead_fits_memory', 'actual_model_generations']}))
