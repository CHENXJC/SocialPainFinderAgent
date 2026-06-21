"""Load and standardize user-provided comments from supported sources."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd


LIKELY_TEXT_COLUMNS = (
    "comment", "comments", "text", "review", "reviews", "feedback", "content",
    "message", "body", "description", "评论", "评价", "内容", "反馈",
)


def _standardize(texts: pd.Series, source: str) -> pd.DataFrame:
    """Return the common loader schema without cleaning or removing rows."""
    frame = pd.DataFrame({"source": source, "text": texts})
    frame.insert(0, "comment_id", range(1, len(frame) + 1))
    return frame[["comment_id", "source", "text"]]


def _table_to_comments(table: pd.DataFrame, source: str) -> pd.DataFrame:
    """Choose a likely comment column, or join all text columns by row."""
    if table.empty:
        return pd.DataFrame(columns=["comment_id", "source", "text"])

    column_lookup = {str(column).strip().casefold(): column for column in table.columns}
    selected = next(
        (column_lookup[name] for name in LIKELY_TEXT_COLUMNS if name in column_lookup),
        None,
    )
    if selected is not None:
        texts = table[selected]
    else:
        text_columns = list(table.select_dtypes(include=["object", "string"]).columns)
        if not text_columns:
            raise ValueError("No text-like columns were found in this file.")
        texts = table[text_columns].apply(
            lambda row: " | ".join(str(value) for value in row if pd.notna(value)), axis=1
        )
    return _standardize(texts, source)


def load_file(file_object: BinaryIO, filename: str) -> pd.DataFrame:
    """Load one CSV, XLSX, or TXT file into the standardized schema."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        raw = file_object.read()
        last_error: Exception | None = None
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
            try:
                return _table_to_comments(pd.read_csv(BytesIO(raw), encoding=encoding), filename)
            except (UnicodeDecodeError, pd.errors.ParserError) as exc:
                last_error = exc
        raise ValueError(f"Could not read the CSV file: {last_error}")

    if suffix == ".xlsx":
        sheets = pd.read_excel(file_object, sheet_name=None, engine="openpyxl")
        frames = [
            _table_to_comments(sheet, f"{filename}:{sheet_name}")
            for sheet_name, sheet in sheets.items()
            if not sheet.empty
        ]
        return combine_inputs(frames)

    if suffix == ".txt":
        raw = file_object.read()
        if isinstance(raw, str):
            text = raw
        else:
            text = ""
            for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
                try:
                    text = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if not text:
                raise ValueError("Could not decode the TXT file.")
        return _standardize(pd.Series(text.splitlines(), dtype="object"), filename)

    raise ValueError("Unsupported file type. Please use CSV, XLSX, or TXT.")


def load_manual_text(text: str, source: str = "manual_input") -> pd.DataFrame:
    """Treat each pasted line as one candidate comment."""
    return _standardize(pd.Series(text.splitlines(), dtype="object"), source)


def combine_inputs(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Combine loader results and assign unique sequential comment IDs."""
    usable = [frame for frame in frames if frame is not None and not frame.empty]
    if not usable:
        return pd.DataFrame(columns=["comment_id", "source", "text"])
    combined = pd.concat(usable, ignore_index=True)
    combined["comment_id"] = range(1, len(combined) + 1)
    return combined[["comment_id", "source", "text"]]


def load_path(path: str | Path) -> pd.DataFrame:
    """Load a local file path; useful for tests and scripts."""
    path = Path(path)
    with path.open("rb") as handle:
        return load_file(handle, path.name)

