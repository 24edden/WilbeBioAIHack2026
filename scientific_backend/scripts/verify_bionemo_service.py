#!/usr/bin/env python3
"""One durable NVIDIA monomer request, solely an engineering integration check."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config import RUNTIME  # Loads the existing private .env without printing it.
import httpx

SOURCE_URL = "https://docs.nvidia.com/nim/bionemo/boltz2/1.7.0/getting-started.html"
API_SOURCE_URL = "https://docs.api.nvidia.com/nim/reference/mit-boltz2-infer"
ENDPOINT = "https://health.api.nvidia.com/v1/biology/mit/boltz2/predict"
# Exact NVIDIA Getting Started / Starting the NIM Container / step 5 example.
SEQUENCE = "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN"
LIMITATIONS = [
    "ENGINEERING INTEGRATION CHECK ONLY: official NVIDIA monomer example, unrelated to CAR-T resistance.",
    "Does not qualify CD19 target retention, a CAR binder, a candidate design or a matched molecular comparison.",
    "Confidence and coordinates are model outputs, not measured folding quality, affinity or biological efficacy.",
    "No production matched-complex capability or hypothesis decision is marked verified by this script.",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode()+b"\n"


def persist(path, value, *, exclusive=False):
    """Fsync bytes and directory; intent is exclusive and never overwritten."""
    data = encoded(value)
    target = path if exclusive else path.with_name(path.name+".tmp")
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC), 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    if not exclusive: os.replace(target, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def save_bytes(path, data):
    with path.open('xb') as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())


def redact(text):
    for name in ("NGC_API_KEY", "NVIDIA_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(name)
        if value: text = text.replace(value, "[REDACTED]")
    return re.sub(r"(?i)bearer\s+[^\s\"']+", "Bearer [REDACTED]", text)


def validate_monomer(cif):
    from Bio.PDB import MMCIFParser
    from Bio.SeqUtils import seq1
    if not isinstance(cif, str) or not cif.lstrip().startswith('data_'):
        raise ValueError("Returned structure is not mmCIF")
    structure = MMCIFParser(QUIET=True, auth_chains=False, auth_residues=False).get_structure('engineering', io.StringIO(cif))
    models = list(structure.get_models())
    if len(models) != 1: raise ValueError("Expected exactly one structural model")
    chains = list(models[0].get_chains())
    if len(chains) != 1 or chains[0].id != 'A': raise ValueError("Expected exactly one chain A")
    residues = list(chains[0].get_residues())
    observed = ''.join(seq1(res.get_resname(), undef_code='X') for res in residues)
    if observed != SEQUENCE: raise ValueError("Observed complete chain sequence differs from submitted official sample")
    if [r.id[1] for r in residues] != list(range(1, len(SEQUENCE)+1)) or any('CA' not in r for r in residues):
        raise ValueError("Residue numbering or alpha-carbon coverage is incomplete")
    atoms = list(structure.get_atoms())
    if not atoms or any(not all(math.isfinite(float(x)) for x in atom.coord) for atom in atoms):
        raise ValueError("Coordinates are empty or nonfinite")
    return {"models":1,"chain_ids":["A"],"residues":len(residues),"atom_count":len(atoms),
            "exact_sequence_match":True,"sequence_sha256":sha(observed),"coordinates_finite":True,"alpha_carbon_coverage_complete":True}


def run_check(check_id, output_root, timeout=300):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', check_id): raise ValueError("Use a unique safe check ID")
    if not math.isfinite(timeout) or not 1 <= timeout <= 900: raise ValueError("Timeout must be 1–900 seconds")
    key = os.getenv('NGC_API_KEY') or os.getenv('NVIDIA_API_KEY')
    if not key: raise ValueError("NVIDIA credential is not configured; no request was sent")
    directory = Path(output_root).resolve()/check_id
    # The directory itself is the duplicate-dispatch guard. Even an incomplete
    # earlier attempt must be investigated, never blindly reused or removed.
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    payload = {"polymers":[{"id":"A","molecule_type":"protein","sequence":SEQUENCE}],
               "recycling_steps":3,"sampling_steps":50,"diffusion_samples":1,"step_scale":1.638,"output_format":"mmcif"}
    request_bytes = encoded(payload)
    save_bytes(directory/'request.json', request_bytes)
    state = {"check_id":check_id,"status":"intent_recorded","scope":"engineering_monomer_only","model":"mit/boltz2",
             "backend":"hosted","endpoint":ENDPOINT,"created_at":now(),"source_url":SOURCE_URL,
             "source_locator":"Starting the NIM Container, step 5, monomer Python/curl request; documentation version 1.7.0",
             "api_source_url":API_SOURCE_URL,"source_verified_at":"2026-09-19","sequence_length":len(SEQUENCE),"sequence_sha256":sha(SEQUENCE),
             "request_file_sha256":sha(request_bytes),"posts_dispatched":0,"artifacts":[],"limitations":LIMITATIONS,
             "monomer_service_verified":False,"matched_comparison_verified":False,"cart_hypothesis_tested":False}
    persist(directory/'intent.json', state, exclusive=True)
    receipt = directory/'receipt.json'
    persist(receipt, state)
    headers = {"Authorization":"Bearer "+key,"Content-Type":"application/json","Accept":"application/json"}
    try:
        state.update(status='dispatched',posts_dispatched=1,dispatched_at=now())
        persist(receipt, state)
        # No retries, redirects, polling, comparison request or model fallback.
        with httpx.Client(transport=httpx.HTTPTransport(retries=0), timeout=httpx.Timeout(timeout,connect=15), follow_redirects=False) as client:
            with client.stream('POST', ENDPOINT, headers=headers, content=request_bytes) as response:
                state.update(http_status=response.status_code,request_id=response.headers.get('nvcf-reqid') or response.headers.get('x-request-id'),response_headers_received_at=now())
                persist(receipt, state)
                chunks=[]; total=0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > 10_000_000: raise ValueError('Response exceeded 10 MB integration-check bound')
                    chunks.append(chunk)
                raw=b''.join(chunks)
        response_text=redact(raw.decode('utf-8', errors='replace'))
        save_bytes(directory/'response.txt', response_text.encode())
        state.update(response_file_sha256=sha(response_text),response_bytes=total,response_received_at=now())
        if state['http_status'] == 202:
            state.update(status='pending',detail='Vendor accepted the request; preserve its ID. No polling or resubmission was performed.')
        elif state['http_status'] != 200:
            state.update(status='failed',detail=f"Vendor returned HTTP {state['http_status']}; redacted response retained. No resubmission was performed.")
        else:
            result=json.loads(response_text)
            structures=result.get('structures'); scores=result.get('confidence_scores')
            if not isinstance(structures,list) or len(structures)!=1 or not isinstance(scores,list) or len(scores)!=1:
                raise ValueError('Expected exactly one structure and one confidence score')
            score=scores[0]
            if isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=1:
                raise ValueError('Confidence score must be finite and within [0,1]')
            item=structures[0]
            if not isinstance(item,dict) or item.get('format')!='mmcif': raise ValueError('Expected mmCIF structure output')
            cif=item.get('structure')
            if isinstance(cif,str): save_bytes(directory/'prediction.cif',cif.encode())
            validation=validate_monomer(cif)
            state.update(status='completed',monomer_service_verified=True,confidence_score=score,validation=validation,
                         artifacts=[{"name":"prediction.cif","path":str(directory/'prediction.cif'),"sha256":sha(cif),"media_type":"chemical/x-mmcif"}],
                         detail='Official monomer request returned one validated sequence-matched structure. Engineering service check only.')
    except BaseException as exc:
        unknown=isinstance(exc,(httpx.TransportError,KeyboardInterrupt,SystemExit))
        state.update(status='unknown' if unknown else 'failed',detail=redact(f'{type(exc).__name__}: {exc}')[:700])
        if unknown: state['detail']='The request may still be running remotely. Do not resubmit. '+state['detail']
    finally:
        state['finished_at']=now()
        persist(receipt,state)
    return {"check_id":check_id,"status":state['status'],"receipt":str(receipt),"request_id":state.get('request_id'),"scope":state['scope']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-id',required=True,help='New unique ID; any existing directory is refused')
    parser.add_argument('--output-dir',type=Path,default=RUNTIME/'engineering',help='Parent directory for the unique check directory')
    parser.add_argument('--timeout',type=float,default=300)
    args=parser.parse_args()
    def interrupted(_signal,_frame): raise KeyboardInterrupt('Local engineering check interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    try: result=run_check(args.check_id,args.output_dir,args.timeout)
    except Exception as exc:
        result={"check_id":args.check_id,"status":"not_dispatched","receipt":None,"detail":redact(f'{type(exc).__name__}: {exc}')[:500]}
    print(json.dumps(result,sort_keys=True))
    # Application receipt carries failure status. Brev retries nonzero remote
    # exits, which is unsuitable for a non-idempotent external inference call.
    return 0


if __name__=='__main__': raise SystemExit(main())
