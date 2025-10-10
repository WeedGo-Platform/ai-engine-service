"""
Localization V2 API

DDD-powered multi-language translation management using the Localization bounded context.

Features:
- Translation management (create, update, publish, deprecate)
- Multi-language support (EN, FR, ES, PT, ZH)
- Translation key namespaces (product, ui, email, etc.)
- Pluralization support for proper grammar
- Translation completion tracking
- Draft → Review → Published workflow
- Fallback to source language
- Character limit validation for UI strings
- Translation statistics and reporting

Supported Languages:
- English (en)
- French (fr)
- Spanish (es)
- Portuguese (pt)
- Chinese (zh)
"""

from .localization_endpoints import router

__all__ = ["router"]
