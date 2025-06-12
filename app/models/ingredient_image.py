#ingredient_image.py

from __future__ import annotations

from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class IngredientImage(SQLModel, table=True):
    """
    Linking table for the many-to-many relationship between Ingredient and Image.
    Used as a link_model in SQLModel for direct many-to-many relationships.
    """
    # Composite Primary Key for the linking table, composed of foreign keys
    ingredient_id: int = Field(
        foreign_key="ingredient.ingredient_id", primary_key=True,
        description="Foreign key to the Ingredient table."
    )
    image_id: int = Field(
        foreign_key="image.image_id", primary_key=True,
        description="Foreign key to the Image table."
    )

    sort_order: Optional[int] = Field(
        default=10,
        description='Used to predefine sort order for display purposes.'
    )

IngredientImage.ingredient = Relationship(back_populates="image_links")
IngredientImage.images = Relationship(back_populates="ingredient_links")
