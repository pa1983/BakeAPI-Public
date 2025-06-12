# from __future__ import annotations # Essential for deferred type evaluation

from sqlmodel import Field, Column, TIMESTAMP, text, select, SQLModel
from app.database.session import Session, engine
from app.models.scratch2 import *

with Session(engine) as session:
    statement = (
        select(Ingredient, Ingredient_Image, Image)
        .select_from(Ingredient)
        .join(Ingredient_Image)
        .join(Image)


    )
    # statement = (select(Ingredient_Image))
    # statement = (select(Ingredient))
    results = session.exec(statement).all()
    for x in results:
        print(results)
