import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel, func

# Forward references for relationships to be defined in other files
# from .ingredient import Ingredient
# from .buyable import Buyable


class IngredientBuyableBase(SQLModel):
    """
    Base model for the ingredient-buyable link.
    Contains all fields that are provided upon creation.
    """
    ingredient_id: int = Field(foreign_key="ingredient.ingredient_id")
    buyable_id: int = Field(foreign_key="buyable.id")
    sort_order: Optional[int] = Field(
        default=10,
        description="Preference order for ingredient maps",
    )
    notes: Optional[str] = Field(default=None, max_length=500)


class IngredientBuyable(IngredientBuyableBase, table=True):
    """
    Main database table model for the ingredient_buyable junction table.
    """
    __tablename__ = "ingredient_buyable"

    id: Optional[int] = Field(default=None, primary_key=True)
    organisation_id: int = Field(foreign_key="organisation.organisation_id")
    # Timestamps managed by the database
    created_timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        nullable=False,
        description="Log of when the entry was created",
    )
    modified_timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        nullable=False,
        sa_column_kwargs={
            "onupdate": func.now()  # Corresponds to ON UPDATE CURRENT_TIMESTAMP
        },
    )

    # --- Relationships ---
    ingredient: "Ingredient" = Relationship()
    buyable: "Buyable" = Relationship()


class IngredientBuyableCreate(IngredientBuyableBase):
    """
    Model used for creating a new ingredient-buyable link via an API.
    Identical to the Base model.
    """
    pass


class IngredientBuyableRead(IngredientBuyableBase):
    """
    Model for reading/returning an ingredient-buyable link from the API.
    Includes all database-generated fields like id and timestamps.
    """
    id: int
    created_timestamp: datetime.datetime
    modified_timestamp: datetime.datetime


class IngredientBuyableUpdate(SQLModel):
    """
    Model for updating an existing ingredient-buyable link.
    Contains only the fields that are user-modifiable. All fields are
    optional to allow for partial updates (PATCH requests).
    """
    sort_order: Optional[int] = None
    notes: Optional[str] = None