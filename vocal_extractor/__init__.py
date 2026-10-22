"""High-quality vocal stem extraction built on Roformer separation models."""

from .pipeline import ExtractionOptions, extract

__all__ = ["ExtractionOptions", "extract"]
