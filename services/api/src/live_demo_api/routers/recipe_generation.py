"""Recipe generation router compatibility module.

The concrete generation route is mounted on ``recipes.router`` at
``/api/v1/products/{product_id}/recipes/generate`` so recipe operations remain
grouped under one product-scoped router.
"""

from __future__ import annotations

from live_demo_api.routers.recipes import generate_recipe

__all__ = ["generate_recipe"]
