"""Anonymous HTTP checks: no token, cookie or authorization header is sent."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--curl',default='curl');args=parser.parse_args()
    paths=['README.md','LICENSE','models/model_card.json',
           'deliverables/CycleTwin_architecture.pdf','deliverables/CycleTwin_architecture.pptx',
           'deliverables/CycleTwin_pitch_deck.pdf','deliverables/CycleTwin_pitch_deck.pptx']
    checks=[]
    for path in paths:
        url='https://raw.githubusercontent.com/kushagragupta2005/CycleTwin_VIT/main/'+path
        r=subprocess.run([args.curl,'-L','-sS','--max-time','30','-o','/dev/null','-w','%{http_code}',url],text=True,capture_output=True)
        checks.append({'path':path,'url':url,'http_status':r.stdout.strip(),'process_returncode':r.returncode,
                       'pass':r.returncode==0 and r.stdout.strip()=='200','error':r.stderr.strip()})
    out={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'authentication':'none',
         'all_pass':all(c['pass'] for c in checks),'checks':checks}
    (ROOT/'docs/public_access_check.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    if not out['all_pass']: raise SystemExit(1)


if __name__=='__main__':main()
