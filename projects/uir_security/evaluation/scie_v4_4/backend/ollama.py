from dataclasses import dataclass
import json
import subprocess
import threading
import time
import urllib.error
import urllib.request

from ..common import digest, now

ALLOWED_ENDPOINTS = ('http://127.0.0.1:11434', 'http://127.0.0.1:11444')
GPU_FIELDS = ('index','uuid','name','memory.total','memory.used','utilization.gpu','driver_version',
              'pcie.link.gen.current','pcie.link.width.current')


def gpu_snapshot():
    try:
        r = subprocess.run(['nvidia-smi','--query-gpu='+','.join(GPU_FIELDS),'--format=csv,noheader,nounits'],
                           capture_output=True, text=True, timeout=8, check=True)
        return [dict(zip(GPU_FIELDS, map(str.strip, line.split(',')))) for line in r.stdout.splitlines()]
    except (OSError, subprocess.SubprocessError) as e:
        return [{'error':str(e)}]


class Probe:
    def __init__(self, interval=1.0):
        self.stop = threading.Event()
        self.interval = interval
        self.samples = []

    def __enter__(self):
        def poll():
            while not self.stop.is_set():
                self.samples.append({'utc':now(),'devices':gpu_snapshot()})
                self.stop.wait(self.interval)
        self.worker = threading.Thread(target=poll, daemon=True)
        self.worker.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.worker.join(timeout=9)


@dataclass(frozen=True)
class Client:
    endpoint: str
    timeout: int = 60

    def __post_init__(self):
        if self.endpoint not in ALLOWED_ENDPOINTS:
            raise ValueError('Only the registered loopback endpoints are allowed')

    def request(self, route, payload=None):
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        req = urllib.request.Request(self.endpoint + route,
              data=None if payload is None else json.dumps(payload).encode(),
              headers={'Content-Type':'application/json'})
        with urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect()).open(req, timeout=self.timeout) as r:
            return json.loads(r.read(8 * 1024 * 1024))

    def metadata(self):
        return {'version':self.request('/api/version')['version'], 'endpoint':self.endpoint,
                'models':self.request('/api/tags')['models']}

    def generate(self, model, system, prompt, options):
        payload = {'model':model['name'],'system':system,'prompt':prompt,'format':'json',
                   'stream':False,'keep_alive':'2m','options':options}
        receipt = {'model':model['name'],'model_digest':model['digest'],'request':payload,
                   'prompt_sha256':digest({'system':system,'prompt':prompt}),'request_sha256':digest(payload),
                   'started_utc':now(),'physical_request_attempted':True,'retry_index':0}
        start = time.monotonic()
        try:
            response = self.request('/api/generate', payload)
            receipt['response'] = response
            status = classify(response, options)
        except urllib.error.HTTPError as e:
            response = e.read(131072).decode(errors='replace')
            receipt.update(http_status=e.code, raw_error=response)
            status = error_status(response)
        except (OSError, ValueError) as e:
            reason = getattr(e,'reason',e)
            receipt['raw_error'] = str(reason)
            status = 'TIMEOUT' if isinstance(reason,TimeoutError) else error_status(str(reason))
        receipt.update(status=status, wall_s=time.monotonic()-start, ended_utc=now())
        return receipt


def error_status(error):
    text = error.lower()
    if 'out of memory' in text or 'cuda oom' in text:
        return 'CUDA_OOM'
    if 'context' in text and ('length' in text or 'truncat' in text):
        return 'CONTEXT_TRUNCATED'
    if 'model' in text and ('load' in text or 'not found' in text):
        return 'MODEL_ERROR'
    return 'BACKEND_ERROR'


def classify(response, options):
    if not isinstance(response,dict):
        return 'BACKEND_ERROR'
    if 'error' in response:
        return error_status(str(response['error']))
    if response.get('done') is not True or response.get('done_reason') != 'stop':
        return 'INCOMPLETE_RESPONSE'
    if not isinstance(response.get('response'),str) or not response['response'].strip():
        return 'INVALID_OUTPUT'
    tokens = response.get('prompt_eval_count')
    if not isinstance(tokens,int) or not isinstance(response.get('eval_count'),int):
        return 'INCOMPLETE_RESPONSE'
    if tokens >= options['num_ctx']-options['num_predict']:
        return 'CONTEXT_TRUNCATED'
    return 'COMPLETED'
