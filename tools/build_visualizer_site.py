"""Package existing previews for static hosting; does not regenerate geometry.

Only standard-library Python is required. Embedded gzip payloads become cached
binary assets, Three.js modules become shared files, and frame URLs are relative
so the same bundle works beneath a GitHub project Pages path.
"""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'engineering/channel-allocation/single-stencil-preview'
OUT=ROOT/'docs'

LOADER="""async function loadAsset(id){
 const response=await fetch(new URL($(id).dataset.src,document.baseURI));
 if(!response.ok)throw new Error(`Geometry download failed (${response.status}). Reload to retry.`);
 const total=Number(response.headers.get('content-length'))||0;
 const reader=response.body.getReader(),chunks=[];let length=0;
 const status=$('status')||$('stats');
 while(true){const {done,value}=await reader.read();if(done)break;chunks.push(value);length+=value.length;
  if(status)status.textContent=`Loading geometry · ${(length/1048576).toFixed(1)}${total?` / ${(total/1048576).toFixed(1)}`:''} MB`;
 }
 const bytes=new Uint8Array(length);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
 return bytes;
}
"""

def sanitize(value):
    if isinstance(value,dict):return {key:sanitize(v) for key,v in value.items()}
    if isinstance(value,list):return [sanitize(v) for v in value]
    if isinstance(value,str):
        normalized=value.replace('\\','/')
        root=ROOT.as_posix()+'/'
        if normalized.lower().startswith(root.lower()):return normalized[len(root):]
        if re.match(r'^[A-Za-z]:/',normalized):return Path(normalized).name
    return value

def build(source=SOURCE,out=OUT):
    out.mkdir(parents=True,exist_ok=True);(out/'assets').mkdir(exist_ok=True);(out/'vendor').mkdir(exist_ok=True)
    manifest={'format':1,'preview':'single-stencil','layouts':[52,56,64],'files':{},'geometry_regenerated':False}
    def write(relative,raw):
        if isinstance(raw,str):raw=raw.encode()
        (out/relative).write_bytes(raw)
        manifest['files'][relative]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    hub=(ROOT/'engineering/channel-allocation/single_stencil_hub.html').read_text(encoding='utf-8')
    assert 'url=`/${layout}-${view}.html`' in hub
    hub=hub.replace('url=`/${layout}-${view}.html`','url=`./${layout}-${view}.html`')
    hub=hub.replace('<title>Single-stencil experiment</title>','<title>LED channel geometry visualizer</title>')
    write('index.html',hub)
    for count in [52,56,64]:
        report=sanitize(json.loads((source/f'{count}-report.json').read_text()))
        write(f'assets/{count}-report.json',json.dumps(report,indent=2)+'\n')
        for kind in ['2d','3d']:
            html=(source/f'{count}-{kind}.html').read_text(encoding='utf-8')
            pattern=r'(<script id="payload" type="application/octet-stream">)(.*?)(</script>)'
            found=re.search(pattern,html,re.S);assert found,(count,kind)
            packed=base64.b64decode(found[2].strip())
            if kind=='2d':
                model=sanitize(json.loads(gzip.decompress(packed)))
                packed=gzip.compress(json.dumps(model,separators=(',',':')).encode(),mtime=0)
            write(f'assets/{count}-{kind}.bin',packed)
            html=html[:found.start()]+f'<script id="payload" type="application/octet-stream" data-src="./assets/{count}-{kind}.bin"></script>'+html[found.end():]
            html=html.replace('try{',LOADER+'\ntry{',1)
            if kind=='2d':
                html,n=re.subn(r"const encoded=\$\('payload'\).*?const text=", "const bytes=await loadAsset('payload');\n const text=",html,count=1,flags=re.S);assert n==1
            else:
                html,n=re.subn(r"const encoded=\$\('payload'\).*?const raw=", "const packed=await loadAsset('payload');\n const raw=",html,count=1,flags=re.S);assert n==1
                pattern=r'(<script type="importmap">)(.*?)(</script>)'
                match=re.search(pattern,html,re.S);assert match
                imports=json.loads(match[2])['imports'];mapping={}
                for name,url in imports.items():
                    filename='three.module.js' if name=='three' else 'OrbitControls.js'
                    code=base64.b64decode(url.split(',',1)[1])
                    relative='vendor/'+filename
                    if relative in manifest['files']:assert (out/relative).read_bytes()==code
                    else:write(relative,code)
                    mapping[name]='./'+relative
                html=html[:match.start()]+match[1]+json.dumps({'imports':mapping})+match[3]+html[match.end():]
                pattern=r'(<script id="model" type="application/json">)(.*?)(</script>)'
                match=re.search(pattern,html,re.S);assert match
                model=sanitize(json.loads(match[2]))
                html=html[:match.start()]+match[1]+json.dumps(model,separators=(',',':'))+match[3]+html[match.end():]
            assert '127.0.0.1' not in html and 'C:/Users/' not in html
            write(f'{count}-{kind}.html',html)
    write('vendor/LICENSE.three.txt',(ROOT/'tools/visualizer-assets/THREE-LICENSE.txt').read_bytes())
    write('.nojekyll','')
    content_id=hashlib.sha256(json.dumps(manifest['files'],sort_keys=True).encode()).hexdigest()
    write('version.json',json.dumps({'preview':'single-stencil','layouts':[52,56,64],'body_black_layers':1,'mating_layer':67,'X':[6,9],'content_id':content_id},indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Packaged {len(manifest["files"])} files, {sum(v["bytes"] for v in manifest["files"].values())/1048576:.1f} MiB in {out}')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=SOURCE);parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();build(args.source,args.output)
