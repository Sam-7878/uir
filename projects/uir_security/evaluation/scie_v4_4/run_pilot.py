"""Hardware/response pilot; no final outcomes or scientific effect claims."""
import argparse
import importlib.metadata
import json
import platform
import subprocess

from .adaptive import note
from .backend import Client, Probe, gpu_snapshot
from .common import TASK, append, load, now, write
from .dataset import SYSTEM, runtime_prompt

MODELS=('phi3.5:latest','qwen2.5:7b')
OPTIONS={'temperature':0,'seed':441108,'num_ctx':4096,'num_predict':176,'main_gpu':0}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--endpoint',default='http://127.0.0.1:11434')
    ap.add_argument('--run-id',default='r2',choices=('r2',))
    args=ap.parse_args()
    client=Client(args.endpoint)
    meta=client.metadata()
    models=[next(r for r in meta['models'] if r['name']==name) for name in MODELS]
    dev=load(TASK/'private/datasets/pilot_runtime.json')
    if len(dev)!=40:
        raise ValueError('Pilot must have 20 benign and 20 attack cases')
    manifest=TASK/'manifests/V4_4_HARDWARE_PILOT_R2.json'
    env={'platform':platform.platform(),'os_release':platform.freedesktop_os_release(),'python':platform.python_version(),
         'gpu_before':gpu_snapshot(),'backend_version':meta['version'],'endpoint':args.endpoint,'models':models,
         'options':OPTIONS,'raw_phase':'development hardware pilot only','started_utc':now(),
         'packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()
                     if d.metadata['Name'] in ('torch','nvidia-cudnn-cu13','pytest','scipy','transformers')}}
    try:
        env['nvidia_smi_header']=subprocess.check_output(['nvidia-smi'],text=True,timeout=8).splitlines()[:3]
    except (OSError,subprocess.SubprocessError):
        env['nvidia_smi_header']=None
    write(manifest,env,exclusive=True)
    for model in models:
        consecutive_errors=0
        with Probe() as probe:
            for item in dev:
                surface=item.get('attack_surface')
                injection=note(surface,0) if surface else ''
                rec=client.generate(model,SYSTEM,runtime_prompt(item,injection),OPTIONS)
                if rec['status']=='COMPLETED':
                    try:
                        v=json.loads(rec['response']['response'])
                        rec['pilot_json_object']=isinstance(v,dict)
                    except ValueError:
                        rec['pilot_json_object']=False
                append(TASK/'raw_runs/pilot_r2_physical.jsonl',{'case_id':item['id'],'attack_input':bool(surface),**rec})
                print(model['name'],item['id'],rec['status'],round(rec['wall_s'],3),flush=True)
                consecutive_errors=consecutive_errors+1 if rec['status'] in ('BACKEND_ERROR','CUDA_OOM','MODEL_ERROR','TIMEOUT') else 0
                if consecutive_errors>=4:
                    break
            loaded=client.request('/api/ps')
        write(TASK/'audits'/f'pilot_gpu_{model["name"].split(":")[0]}.json',
              {'model':model['name'],'gpu_samples':probe.samples,'ollama_ps':loaded},exclusive=True)
        client.request('/api/generate',{'model':model['name'],'keep_alive':0})
    print('Pilot 80 planned physical attempts finished',flush=True)

if __name__=='__main__':
    main()
