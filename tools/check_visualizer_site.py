"""Verify static bundle hashes, geometry contracts and publication boundaries."""
from pathlib import Path
import argparse,ast,gzip,hashlib,json,re

def check(site):
    manifest=json.loads((site/'manifest.json').read_text())
    assert set(p.relative_to(site).as_posix() for p in site.rglob('*') if p.is_file())==set(manifest['files'])|{'manifest.json'}
    for name,info in manifest['files'].items():
        file=site/name;raw=file.read_bytes()
        assert len(raw)==info['bytes'] and hashlib.sha256(raw).hexdigest()==info['sha256'],name
        assert len(raw)<50*1024*1024,('File too large for normal Git hosting',name)
        if file.suffix in ['.html','.js','.json','.txt']:
            text=raw.decode()
            assert not re.search(r'(?:C:[/\\]Users[/\\]|127\.0\.0\.1|github_pat_|ghp_[A-Za-z0-9]{20}|BEGIN OPENSSH PRIVATE)',text),name
    hub=(site/'index.html').read_text()
    assert 'url=`./${layout}-${view}.html`' in hub
    for count in [52,56,64]:
        flat=json.loads(gzip.decompress((site/f'assets/{count}-2d.bin').read_bytes()))
        for key in ['x9','x6','x0']:assert len(flat['variants'][key]['layers'])==67
        assert flat['variants']['x9']['layers'][-1]['path']==flat['variants']['x6']['layers'][-1]['path']
        assert flat['variants']['x9']['layers'][-1]['path']!=flat['variants']['x0']['layers'][-1]['path']
        assert flat['weights'][-1]==0 and flat['weights'][-2]>0
        assert flat['report']['body_black_stencil_layers']==1 and flat['report']['pin_height_mm']==.2
        assert all(flat['report']['variants'][str(x)]['lower_source_chambers_isolated'] for x in [6,9])
        html=(site/f'{count}-3d.html').read_text()
        data=json.loads(re.search(r'<script id="model" type="application/json">(.*?)</script>',html,re.S)[1])
        assert data['matingLayer']==67
        assert all(len(data['variantsPrint'][str(x)])==68 for x in [0,6,9])
        expected=max(max(d['position']['offset']+d['position']['count']*4,d['index']['offset']+d['index']['count']*4) for d in data['meshes'])
        actual=0
        with gzip.open(site/f'assets/{count}-3d.bin','rb') as stream:
            while chunk:=stream.read(8*1024*1024):actual+=len(chunk)
        assert actual==expected,(count,actual,expected)
    root=Path(__file__).resolve().parents[1]
    for name in ['build_visualizer_site.py','check_visualizer_site.py']:
        p=root/'tools'/name;ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    print('PASS: asset integrity, publication boundaries, binary layouts, geometry endpoints, X variants and Python syntax')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--site',type=Path,default=Path(__file__).resolve().parents[1]/'docs')
    check(parser.parse_args().site)
