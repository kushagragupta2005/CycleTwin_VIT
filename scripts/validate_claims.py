"""Check both authored text and metric tokens against freshly generated claims."""
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
NUMBER=re.compile(r'(?<![\w.])\d+\.\d+%?(?![\w.])')


def normalize(s):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s)).strip()


def required_strings(slide, architecture=None):
    values=[slide['title'],slide['subtitle'],slide['footer'],*slide.get('body',[])]
    for row in slide.get('table') or []: values.extend(map(str,row))
    if slide.get('diagram'): values.extend((architecture or slide)['nodes'])
    return values


def check_text(text, expected, name):
    normalized=normalize(text)
    for value in expected:
        if normalize(value) not in normalized:
            raise AssertionError(f'{name}: text/claim missing: {value}')
    allowed=set(NUMBER.findall(' '.join(expected)))
    extra=set(NUMBER.findall(text))-allowed
    if extra: raise AssertionError(f'{name}: metric strings absent from claims: {sorted(extra)}')


def validate_pptx(path, slides, architecture):
    with zipfile.ZipFile(path) as z:
        names=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)],
                     key=lambda n:int(re.search(r'(\d+)\.xml',n).group(1)))
        if len(names)!=len(slides): raise AssertionError('Slide count differs from claims')
        for name,slide in zip(names,slides):
            root=ET.fromstring(z.read(name))
            text=' '.join(x.text or '' for x in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'))
            check_text(text,required_strings(slide,architecture),str(path)+':'+name)


def validate_pdf(path,slides,architecture):
    from pypdf import PdfReader
    reader=PdfReader(path)
    if len(reader.pages)!=len(slides): raise AssertionError('PDF page count differs from claims')
    for i,(page,slide) in enumerate(zip(reader.pages,slides)):
        check_text(page.extract_text(),required_strings(slide,architecture),str(path)+':'+str(i))


def main():
    c=json.loads((ROOT/'docs/claims.json').read_text()); arch=c['deliverables']['architecture']
    expected={f'{name}.{ext}' for name in ('CycleTwin_pitch_deck','CycleTwin_architecture') for ext in ('pptx','pdf')}
    actual={p.name for p in (ROOT/'deliverables').iterdir() if p.suffix in ('.pptx','.pdf')}
    if actual!=expected: raise AssertionError('Unexpected/stale deliverable files: '+repr(actual^expected))
    for name,slides in [('CycleTwin_pitch_deck',c['deliverables']['deck']),
                        ('CycleTwin_architecture',[dict(arch,diagram=True)])]:
        validate_pptx(ROOT/'deliverables'/f'{name}.pptx',slides,arch)
        validate_pdf(ROOT/'deliverables'/f'{name}.pdf',slides,arch)
    if (ROOT/'README.md').read_text()!=c['deliverables']['readme']: raise AssertionError('README differs from generated claims')
    for minutes,text in c['deliverables']['video_scripts'].items():
        if (ROOT/f'docs/video_script_{minutes}min.md').read_text()!=text: raise AssertionError('Video script differs from claims')
    print('PASS: README, scripts, native PPTX and PDF claim strings match generated claims')


if __name__=='__main__': main()
