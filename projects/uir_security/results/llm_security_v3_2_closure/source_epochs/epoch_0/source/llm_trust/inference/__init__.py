"""Inference package."""
from .base import BaseInferenceBackend, GenerationResult
from .ollama_client import OllamaClient
from .renderer import UirPromptRenderer

__all__ = ["BaseInferenceBackend", "GenerationResult", "OllamaClient", "UirPromptRenderer"]
from .phi35_transformers import Phi35TransformersBackend

__all__ = ["Phi35TransformersBackend"]
