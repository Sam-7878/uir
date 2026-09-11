from .core import run_pipeline

NAME = "C5_GUARDRAIL"

def run(case, registry, corpus, model):
    return run_pipeline(NAME, case, registry, corpus, model)
