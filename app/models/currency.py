import decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Currency(SQLModel, table=True):

    currency_code: str = Field(primary_key=True, max_length=5)
    currency_name: str = Field(max_length=50, index=True)
    is_base_currency: Optional[bool] = Field(default=False)
    conversion_rate_to_base: decimal.Decimal = Field(
        max_digits=18, decimal_places=10
    )
    symbol: Optional[str] = Field(max_length=3) # optional to avoid finding all the symbols for now...


