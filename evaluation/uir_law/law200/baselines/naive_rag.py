from .core import run_pipeline

NAME = "C1_NAIVE_RAG"

def run(case, registry, corpus, model):
    return run_pipeline(NAME, case, registry, corpus, model)
