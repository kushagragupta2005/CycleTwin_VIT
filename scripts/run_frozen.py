"""Execute the predeclared frozen evaluation once; refuse existing results or run locks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_eval import main


def acquire_once_lock(path):
    path.parent.mkdir(exist_ok=True,parents=True)
    return os.open(str(path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)


def launch():
    os.chdir(ROOT)
    protocol= json.loads(Path('docs/frozen_protocol.json').read_text())
    tagged=subprocess.check_output(['git','rev-parse',protocol['tag']+'^{commit}'],text=True).strip()
    current=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if tagged!=current: raise RuntimeError('Run the frozen protocol only from its exact tagged commit')
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise RuntimeError('Freeze requires a clean checkout before execution')
    output=Path('results_final_frozen.json')
    if output.exists(): raise FileExistsError('Frozen result already exists; never overwrite it')
    fd=acquire_once_lock(Path('results/frozen_execution.lock'))
    with os.fdopen(fd,'w') as handle:
        json.dump({'tag':protocol['tag'],'commit':tagged,
                   'protocol_sha256':hashlib.sha256(Path('docs/frozen_protocol.json').read_bytes()).hexdigest(),
                   'seeds':protocol['seeds'],'status':'started; lock deliberately survives failures'},handle,indent=2)
    main(seeds=tuple(protocol['seeds']),output_path=str(output),artifact_dir='models/frozen',
         prediction_path='results/predictions_final_frozen.csv',scope='frozen-v1 synthetic primary logistic evaluation')
    receipt={'tag':protocol['tag'],'commit':tagged,'seeds':protocol['seeds'],
             'results_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'status':'completed once'}
    Path('results/frozen_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':launch()
