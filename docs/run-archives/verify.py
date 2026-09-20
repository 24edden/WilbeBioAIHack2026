"""Offline integrity verifier. Usage: python3 verify.py /path/to/extracted/bundle"""
import hashlib,json,pathlib,sys

def digest(value):
    text=value if isinstance(value,str) else json.dumps(value,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(text.encode()).hexdigest()

def resolve(root,relative):
    p=pathlib.PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative:raise ValueError('Unsafe archive path')
    out=root.joinpath(*p.parts)
    if out.is_symlink() or not out.resolve().is_relative_to(root.resolve()):raise ValueError('Archive path escapes root')
    return out

def pointer(document,path):
    if path=='':return document
    if not path.startswith('/'):raise ValueError('Invalid JSON pointer')
    for key in path[1:].split('/'):
        key=key.replace('~1','/').replace('~0','~')
        document=document[int(key)] if isinstance(document,list) else document[key]
    return document

def walk(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from walk(child)
    elif isinstance(value,list):
        for child in value:yield from walk(child)

def verify(root):
    root=pathlib.Path(root).resolve(); files=0; records=0
    checksum_file=root/'checksums.sha256'
    checks={}
    for line in checksum_file.read_text().splitlines():
        expected,path=line.split('  ',1)
        if path in checks:raise ValueError('Duplicate inventory path')
        checks[path]=expected
        if hashlib.sha256(resolve(root,path).read_bytes()).hexdigest()!=expected:raise ValueError('Checksum mismatch: '+path)
        files+=1
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=checksum_file}
    if actual!=set(checks):raise ValueError('Files omitted from or added to checksum inventory')
    manifest=json.loads((root/'manifest.json').read_text())
    if manifest['schema_version']!='team-tbd-archive/1.0.0':raise ValueError('Unsupported manifest')
    seen=set()
    def file_ref(ref):
        data=resolve(root,ref['path']).read_bytes()
        if len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('FileRef mismatch')
        return data
    for obj in walk(manifest):
        if {'path','sha256','bytes','media_type'}.issubset(obj):file_ref(obj)
    for entry in manifest['runs']:
        if entry['run_id'] in seen:raise ValueError('Duplicate run identity')
        seen.add(entry['run_id'])
        raw=json.loads(file_ref(entry['raw_export']));view=json.loads(file_ref(entry['view']));run=raw['run']
        if view['run_id']!=entry['run_id'] or run['id']!=entry['run_id']:raise ValueError('Identity mismatch')
        if view['state']['status']!=run['status'] or entry['status']!=run['status']:raise ValueError('State mismatch')
        if view['hypothesis']!=run['hypothesis']:raise ValueError('Hypothesis changed')
        if digest(run['hypothesis']['text'])!=run['hypothesis']['sha256']:raise ValueError('Hypothesis hash mismatch')
        if digest({'run':run,'case_manifest':raw['case_manifest']})!=raw['content_sha256']:raise ValueError('Application export mismatch')
        for obj in walk(view):
            if {'path','sha256','bytes','media_type'}.issubset(obj):file_ref(obj)
            if 'raw_pointer' in obj and 'data' in obj and obj['raw_pointer'] is not None:
                if pointer(raw,obj['raw_pointer'])!=obj['data']:raise ValueError('Normalized record changed')
                records+=1
        for i,decision in enumerate(run.get('decisions',[]),1):
            if decision['version']!=i or digest({k:v for k,v in decision.items() if k!='sha256'})!=decision['sha256']:
                raise ValueError('Decision version/hash mismatch')
    return {'status':'verified','files':files,'runs':len(seen),'exact_source_records':records,'external_calls':0}

if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
