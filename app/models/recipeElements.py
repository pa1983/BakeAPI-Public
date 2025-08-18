# a wrapper on all recipe link elements
from pydantic import BaseModel
from typing import Literal, Union

from app.models.recipe_ingredient import RecipeIngredientRead
from app.models.recipe_labour import RecipeLabourRead
from app.models.recipe_sub_recipe import RecipeSubRecipeRead


# define the API response elements in the format they will be sent to the front end when
# a request is made for all recipe elements.  'Element type' allows the front end to look up the
# matching handler logic for each data type in a heterogeneous list of elements

class IngredientElement(BaseModel):
    element_type: Literal["ingredient"] = "ingredient"
    data: RecipeIngredientRead

class LabourElement(BaseModel):
    element_type: Literal["labour"] = "labour"
    data: RecipeLabourRead

class SubRecipeElement(BaseModel):
    element_type: Literal["subrecipe"] = "subrecipe"
    data: RecipeSubRecipeRead

# A definition of the union type that can contain a mix of the above element types
RecipeElement= Union[IngredientElement, LabourElement, SubRecipeElement]