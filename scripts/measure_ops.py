"""Measure local synthetic inference operations; output is host-specific evidence."""
import json
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.features import attach_prior_cycle_lengths
from src.generator import generate
from src.inference import predict


def peak_rss_kib():
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return float(value/1024) if sys.platform=='darwin' else float(value)


def run():
    row=next(r for r in attach_prior_cycle_lengths(generate(7001)) if r['cycle']==1)
    # First call validates persisted artifact hashes and warms the in-process model cache.
    predict(row,18,2,seed=7001)
    durations=[]
    for _ in range(1000):
        start=time.perf_counter_ns();predict(row,18,2,seed=7001);durations.append((time.perf_counter_ns()-start)/1e6)
    code="from src.features import attach_prior_cycle_lengths; from src.generator import generate; from src.inference import predict; r=next(x for x in attach_prior_cycle_lengths(generate(7001)) if x['cycle']==1); predict(r,18,2,seed=7001)"
    start=time.perf_counter_ns();proc=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True,check=True);cold_ms=(time.perf_counter_ns()-start)/1e6
    result={'scope':'Local host operations evidence for synthetic persisted inference; not a production service SLA.',
            'host':{'platform':platform.platform(),'python':platform.python_version()},'model':{'seed':7001,'day':18,'tier':2},
            'cold_subprocess_ms':cold_ms,'warm_repeats':len(durations),'warm_latency_ms':{'mean':statistics.mean(durations),'p50':statistics.median(durations),'p95':sorted(durations)[949],'max':max(durations)},
            'process_peak_rss_kib':peak_rss_kib(),'rss_note':'ru_maxrss for this local Python process; macOS reports bytes and the script converts to KiB.'}
    (ROOT/'results_ops.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':run()
