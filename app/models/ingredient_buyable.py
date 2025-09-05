import datetime
from typing import Optional
from sqlalchemy import func
from sqlmodel import Field, Relationship, SQLModel,UniqueConstraint



class IngredientBuyableBase(SQLModel):

    ingredient_id: int = Field(foreign_key="ingredient.ingredient_id")
    buyable_id: int = Field(foreign_key="buyable.id")
    sort_order: Optional[int] = Field(
        default=10,
        description="Preference order for ingredient maps",
    )
    notes: Optional[str] = Field(default=None, max_length=500)


class IngredientBuyable(IngredientBuyableBase, table=True):

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
    __table_args__ = (
        UniqueConstraint("ingredient_id", "buyable_id", name="uq_ingredient_buyable_link"),
    )

    # --- Relationships ---
    ingredient: "Ingredient" = Relationship()
    buyable: "Buyable" = Relationship()


class IngredientBuyableCreate(IngredientBuyableBase):

    pass


class IngredientBuyableRead(IngredientBuyableBase):

    id: int
    created_timestamp: datetime.datetime
    modified_timestamp: datetime.datetime


class IngredientBuyableUpdate(SQLModel):

    sort_order: Optional[int] = None
    notes: Optional[str] = None