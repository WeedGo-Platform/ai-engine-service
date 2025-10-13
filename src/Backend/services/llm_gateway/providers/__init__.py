"""
LLM Providers

Available providers:
- OpenRouterProvider: OpenRouter API (DeepSeek R1, free tier)
- GroqProvider: Groq API (Llama 3.3 70B, ultra-fast)
- LLM7Provider: LLM7.io (anonymous access, NO AUTH NEEDED)
- LocalProvider: Local llama-cpp-python (fallback)
"""

from .base import BaseProvider
from .openrouter import OpenRouterProvider
from .groq import GroqProvider
from .llm7 import LLM7Provider, LLM7GPT4Mini, LLM7GPT4, LLM7Claude
from .local import LocalProvider

__all__ = [
    "BaseProvider",
    "OpenRouterProvider",
    "GroqProvider",
    "LLM7Provider",
    "LLM7GPT4Mini",
    "LLM7GPT4",
    "LLM7Claude",
    "LocalProvider"
]
