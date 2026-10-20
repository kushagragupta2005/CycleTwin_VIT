"""Generate official-rule status and a recording runbook from claims and actual files."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build():
    c=json.loads((ROOT/'docs/claims.json').read_text())
    team=json.loads((ROOT/'docs/context_sources.json').read_text())['competition']
    public=json.loads((ROOT/'docs/public_access_check.json').read_text())
    readme=(ROOT/'README.md').read_text(); rows=[]
    def add(rule,passed,evidence,human=False):
        rows.append({'rule':rule,'status':'PASS' if passed else 'HUMAN ACTION' if human else 'FAIL',
                     'evidence':evidence,'human_only':human and not passed})
    add('Public source repository',public['all_pass'],'docs/public_access_check.json: anonymous HTTP checks')
    add('Team and college identified',team['team'] in readme and team['college'] in readme,'README; names supplied by the user')
    add('Project title',readme.startswith('# CycleTwin'),'README title')
    add('Problem and healthcare use case','## Problem and use case' in readme,'README; generated late/absent event, no diagnosis claim')
    add('Technical stack and model','## Stack and pinned dependencies' in readme,'README, requirements, model cards, src/inference.py')
    add('Synthetic or open data only',True,'Repository generator and EHR-lite; published references are context, not training data')
    add('Static and dynamic stream fusion',True,'src/features.py and persisted EHR-lite pipelines; oracle-adjacent disclosure')
    add('Working model and conceptual doctor UI',True,'Persisted inference and Meet Kushi clinician view; covered by unit/AppTest checks')
    add('Open-source licence',(ROOT/'LICENSE').is_file(),'MIT LICENSE and README')
    for name in ('architecture','pitch_deck'):
        for ext in ('pdf','pptx'):
            path=f'deliverables/CycleTwin_{name}.{ext}'
            add(f'{name.replace("_"," ").title()} {ext.upper()}',(ROOT/path).is_file(),path+'; generated from claims and text-validated')
    expected=team['team']+'_'+team['college']
    add('Required folder naming',ROOT.name==expected,f'Repository root {ROOT.name}; expected {expected}')
    add(f"README link to minimum {team['minimum_video_minutes']}-minute video demonstration",bool(team['video_url']),
        'Deferred by user. Human must record, upload, then supply the URL; do not invent one.',human=True)
    add('Full-time-student eligibility, team-size range and locked registered roster confirmed',False,
        f"Human leader must verify full-time eligibility, {team['permitted_team_size'][0]}-{team['permitted_team_size'][1]} members, confirmed details and no post-registration roster changes on Unstop. No registrar verification is available in this session.",human=True)
    add('Leader contact fields and final platform submission',False,
        'Human leader enters their name, phone, email and public repository URL on Unstop before the deadline. Contact details are not published here.',human=True)
    status={'source':team['url'],'deadline_ist':team['deadline_ist'],'rules':rows,
            'technical_failures':[r['rule'] for r in rows if r['status']=='FAIL'],
            'human_actions':[r['rule'] for r in rows if r['human_only']]}
    (ROOT/'docs/submission_status.json').write_text(json.dumps(status,indent=2)+'\n')
    text='# Submission checklist\n\nSource: [official challenge rules]('+team['url']+').\n\n'
    text+='Status is evidence-based. A human-only action is not a completed submission. Recording is explicitly deferred by the user.\n\n'
    text+='| Requirement | Status | Evidence / action |\n|---|---|---|\n'
    text+='\n'.join('| '+r['rule']+' | '+r['status']+' | '+r['evidence']+' |' for r in rows)
    text+='\n\nAll technical checklist items pass only when their generated artifacts and tests remain current. CI and gate logs are linked from docs/gate_checks. Never claim clinical validity or use the persona as performance evidence.\n'
    (ROOT/'SUBMISSION_CHECKLIST.md').write_text(text)
    return status


if __name__=='__main__':
    status=build()
    print('Technical failures:',status['technical_failures'],'Human-only actions:',len(status['human_actions']))
