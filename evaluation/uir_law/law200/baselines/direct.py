from .core import run_pipeline

NAME = "C0_DIRECT"

def run(case, registry, corpus, model):
    return run_pipeline(NAME, case, registry, corpus, model)
