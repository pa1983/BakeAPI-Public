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
    image_id: int = Field(
        foreign_key="image.image_id", primary_key=True,
        description="Foreign key to the Image table."
    )


class Ingredient_Image(Ingredient_ImageBase, table=True):
    """
    Linking table for the many-to-many relationship between Ingredient and Image.
    Used as a link_model in SQLModel for direct many-to-many relationships.
    """
    id: int = Field(default=None, primary_key=True)
    ingredient_id: int = Field(
        foreign_key="ingredient.ingredient_id",
        description="Foreign key to the Ingredient table."
    )
    organisation_id: int = Field(foreign_key="organisation.organisation_id")  # included desipte violating normalisation guidelines to simplify multi-tenancy enforcement.  No need for linked query to check owner before carry out update

    organisation: "Organisation" = Relationship()

    ingredient: "Ingredient" = Relationship(back_populates="image_links")
    # image: "Image" = Relationship(back_populates="ingredient_links")
    # removed the backpopulates to make the relationship uni-directional and remove need for image to have an ingredient reference - was preventing use of image table in invoices
    image: "Image" = Relationship()


class Ingredient_ImageRead(Ingredient_ImageBase):
    id: int
    sort_order:Optional[int]
    image: ImageRead # single instance rather than a list, as with other M:M links as it can only occur once per Ingredient_Image entry


class Ingredient_ImageCreate(Ingredient_ImageBase):
    pass

class Ingredient_ImageUpdate(Ingredient_ImageBase):
    pass

