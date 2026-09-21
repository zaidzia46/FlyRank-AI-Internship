"""
The shape of a finished record, defined once with Pydantic, plus the
normalization helpers that turn raw scraped text into that shape.
"""
import re
from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator

PRICE_PATTERN = re.compile(r"[\d.]+")
AVAILABLE_COUNT_PATTERN = re.compile(r"\((\d+)\s+available\)")
RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BookRecord(BaseModel):
    """A finished, checked record - this is the only shape that reaches books.json."""

    title: str
    product_url: HttpUrl  # the canonical URL - a record's identity
    price_gbp: float       # clean, numeric
    price_text: str        # original text, kept side by side with the clean value
    in_stock: bool
    stock_count: Optional[int] = None
    availability_text: str
    rating: Optional[int] = None
    rating_text: Optional[str] = None
    description: Optional[str] = None  # optional - null when the page had none
    source_page: str
    fetched_at: str

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v):
        if not v.strip():
            raise ValueError("title must not be blank")
        return v

    @field_validator("price_gbp")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("price_gbp must be greater than 0")
        return v


def normalize_price(price_text: str) -> float:
    """'£51.77' -> 51.77"""
    match = PRICE_PATTERN.search(price_text)
    if not match:
        raise ValueError(f"could not find a number in price_text: {price_text!r}")
    return float(match.group())


def normalize_availability(availability_text: str) -> tuple[bool, Optional[int]]:
    """'In stock (22 available)' -> (True, 22). 'Out of stock' -> (False, None)."""
    in_stock = "in stock" in availability_text.lower()
    match = AVAILABLE_COUNT_PATTERN.search(availability_text)
    stock_count = int(match.group(1)) if match else None
    return in_stock, stock_count


def normalize_rating(rating_text: Optional[str]) -> Optional[int]:
    """'Three' -> 3"""
    if rating_text is None:
        return None
    return RATING_WORDS.get(rating_text)


def raw_to_record(raw: dict) -> BookRecord:
    """Turn one raw extracted dict into a validated BookRecord. Raises on bad data."""
    price_gbp = normalize_price(raw["price_text"])
    in_stock, stock_count = normalize_availability(raw["availability_text"])
    rating = normalize_rating(raw["rating_text"])

    return BookRecord(
        title=raw["title"],
        product_url=raw["product_url"],
        price_gbp=price_gbp,
        price_text=raw["price_text"],
        in_stock=in_stock,
        stock_count=stock_count,
        availability_text=raw["availability_text"],
        rating=rating,
        rating_text=raw["rating_text"],
        description=raw["description"],
        source_page=raw["source_page"],
        fetched_at=raw["fetched_at"],
    )
