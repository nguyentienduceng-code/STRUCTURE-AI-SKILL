import cProfile
import json
import pstats
import runpy
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
target = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
sys.argv = [str(target)]
profiler = cProfile.Profile()
wall, cpu = time.perf_counter(), time.process_time()
code = 0
profiler.enable()
try:
    runpy.run_path(str(target), run_name='__main__')
except SystemExit as exc:
    code = exc.code or 0
finally:
    profiler.disable()
    metrics = {'wall_seconds': time.perf_counter()-wall, 'parent_cpu_seconds': time.process_time()-cpu, 'exit_code': code}
    profiler.dump_stats(str(output.with_suffix('.prof')))
    with output.with_suffix('.txt').open('w', encoding='utf-8') as stream:
        stream.write(json.dumps(metrics)+'\n')
        pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats('cumulative').print_stats(35)
sys.exit(code)
