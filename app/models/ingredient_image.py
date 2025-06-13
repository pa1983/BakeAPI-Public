#ingredient_image.py

from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

from app.models.image import ImageRead


class Ingredient_ImageBase(SQLModel):
    # Composite Primary Key for the linking table, composed of foreign keys

    sort_order: Optional[int] = Field(
        default=10,
        description='Used to predefine sort order for display purposes.'
    )


class Ingredient_Image(Ingredient_ImageBase, table=True):
    """
    Linking table for the many-to-many relationship between Ingredient and Image.
    Used as a link_model in SQLModel for direct many-to-many relationships.
    """
    ingredient_id: int = Field(
        foreign_key="ingredient.ingredient_id", primary_key=True,
        description="Foreign key to the Ingredient table."
    )
    image_id: int = Field(
        foreign_key="image.image_id", primary_key=True,
        description="Foreign key to the Image table."
    )

    ingredient: "Ingredient" = Relationship(back_populates="image_links")
    image: "Image" = Relationship(back_populates="ingredient_links")

class Ingredient_ImageRead(Ingredient_ImageBase):
    sort_order:Optional[int]
    image: ImageRead # single instance rather than a list, as with other M:M links as it can only occur once per Ingredient_Image entry



