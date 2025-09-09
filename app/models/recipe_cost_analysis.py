"""
Defines the SQLModel for parsing the results of the
combined recursive recipe costing query.
"""

from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class RecipeCostAnalysis(SQLModel):
    """
    A single row from the final combined recipe cost analysis query.

    This model captures both labour and ingredient costs (and energy/equipment in future), standardised into a
    uniform structure, and includes analytical data like the percentage of
    the total cost.
    """
    # --- Core Identification Fields ---
    cost_type: str = Field(
        description="The type of cost, e.g., 'Labour' or 'Ingredient'."
    )
    recipe_id: int = Field(
        description="The ID of the recipe this cost item belongs to."
    )
    recipe_name: str = Field(
        description="The name of the recipe this cost item belongs to."
    )
    parent_recipe_id: Optional[int] = Field(
        default=None,
        description="The ID of the parent recipe in the hierarchy. NULL for top-level items."
    )
    item_id: int = Field(
        description="The unique ID of the cost item (e.g., labourer_id or ingredient_id)."
    )
    item_name: str = Field(
        description="The name of the cost item (e.g., 'Head Baker' or 'Flour')."
    )
    item_category: str = Field(
        description="The category of the cost item (e.g., 'Labour' or 'Raw Ingredient')."
    )

    # --- Top-Level Context Fields ---
    top_level_recipe_id: int = Field(
        description="The ID of the top-level recipe being analyzed."
    )
    top_level_recipe_name: str = Field(
        description="The name of the top-level recipe being analyzed."
    )
    top_level_batch_quantity: Decimal = Field(
        description="The total quantity produced by the top-level recipe (e.g., 40 croissants)."
    )
    top_level_uom: str = Field(
        description="The unit of measure for the top-level recipe's quantity (e.g., 'pcs')."
    )

    # --- Calculated Cost and Quantity Fields ---
    total_quantity: Decimal = Field(
        description="The total scaled quantity of this item needed for the top-level recipe."
    )
    unit: str = Field(
        description="The unit of measure for the total_quantity (e.g., 'minutes', 'kg')."
    )
    total_cost: Decimal = Field(
        description="The total calculated cost for this item."
    )
    percentage_of_total_cost: Decimal = Field(
        description="This item's percentage contribution to the grand total cost."
    )


