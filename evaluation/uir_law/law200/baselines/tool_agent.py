from .core import run_pipeline

NAME = "C4_TOOL_AGENT"

def run(case, registry, corpus, model):
    return run_pipeline(NAME, case, registry, corpus, model)
