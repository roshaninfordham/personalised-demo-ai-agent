from __future__ import annotations


class RecipeError(ValueError):
    """Base error for deterministic recipe engine failures."""


class RecipeValidationError(RecipeError):
    """Raised when a caller requires a valid recipe but validation failed."""


class RecipeCompilationError(RecipeError):
    """Raised when a normalized recipe cannot be compiled safely."""
