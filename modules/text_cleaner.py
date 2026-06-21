"""Language-safe cleaning that preserves original evidence."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


def normalize_text(value: object) -> str:
    """Normalize Unicode and whitespace without deleting Chinese or English text."""
    if pd.isna(value):
        return ""
    normalized = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", " ", normalized).strip()


def clean_comments(data: pd.DataFrame) -> pd.DataFrame:
    """Remove empty and duplicate comments while preserving their original text."""
    required = {"comment_id", "source", "text"}
    if not required.issubset(data.columns):
        raise ValueError("Input must contain comment_id, source, and text columns.")

    cleaned = data.rename(columns={"text": "original_text"}).copy()
    cleaned["cleaned_text"] = cleaned["original_text"].map(normalize_text)
    cleaned = cleaned[cleaned["cleaned_text"] != ""].copy()
    cleaned["_duplicate_key"] = cleaned["cleaned_text"].str.casefold()
    cleaned = cleaned.drop_duplicates("_duplicate_key", keep="first")
    return cleaned.drop(columns="_duplicate_key").reset_index(drop=True)

