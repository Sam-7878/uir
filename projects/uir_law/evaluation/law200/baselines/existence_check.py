from .core import run_pipeline

NAME = "C2_EXISTENCE_CHECK"

def run(case, registry, corpus, model):
    return run_pipeline(NAME, case, registry, corpus, model)
