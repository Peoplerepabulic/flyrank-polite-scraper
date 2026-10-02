"""pydantic v2 schema for a scraped book."""

from pydantic import BaseModel, Field, HttpUrl


class Book(BaseModel):
    """One validated book record."""

    title: str = Field(min_length=1)
    price: float = Field(ge=0)
    rating: int = Field(ge=1, le=5)
    in_stock: bool
    product_url: HttpUrl

    model_config = {"str_strip_whitespace": True}
