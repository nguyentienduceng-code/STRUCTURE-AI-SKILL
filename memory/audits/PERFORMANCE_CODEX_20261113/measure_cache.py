import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
records = []
with tempfile.TemporaryDirectory(prefix='pdf_index_benchmark_') as cache:
    for mode in ('cold', 'warm'):
        start = time.perf_counter()
        result = subprocess.run([sys.executable, str(ROOT/'.agents/tests/test_citation_grounding_guard.py')],
                                cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                                env={**os.environ, 'PYTHONUTF8': '1', 'PDF_TEXT_INDEX_CACHE_DIR': cache})
        seconds = time.perf_counter()-start
        (OUT/f'cache_{mode}.log').write_text(result.stdout+'\n'+result.stderr, encoding='utf-8')
        records.append({'mode': mode, 'wall_seconds': seconds, 'exit_code': result.returncode})
(OUT/'cache_timings.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
print(json.dumps(records))
sys.exit(int(any(record['exit_code'] for record in records)))
