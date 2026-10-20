"""Write text deliverables exclusively from generated claims; does not retrain."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    c=json.loads((ROOT/'docs/claims.json').read_text())
    (ROOT/'README.md').write_text(c['deliverables']['readme'])
    for minutes,text in c['deliverables']['video_scripts'].items():
        (ROOT/f'docs/video_script_{minutes}min.md').write_text(text)
    nodes=c['deliverables']['architecture']['nodes']
    (ROOT/'docs/architecture.md').write_text('# Implemented architecture\n\n'+c['deliverables']['architecture']['subtitle']+'\n\n'+'\n\n'.join(nodes)+'\n\nOne fitted prediction path serves benchmark, cohort, patient and Kushi views. EHR-lite is implemented and oracle-adjacent. XML parsing is separate and does not score imports. The reproductive/metabolic illustration does not affect fitted predictions. All project data is synthetic.\n')
    print('Wrote README, video scripts and architecture text from docs/claims.json')


if __name__=='__main__': main()
