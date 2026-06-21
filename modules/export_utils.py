"""Small, local-only helpers for report filenames and filesystem exports."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import pandas as pd


def ensure_output_dir(output_dir: str | Path) -> Path:
    """Create an output directory when needed and return its resolved path."""
    directory = Path(output_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def build_timestamp(moment: datetime | None = None) -> str:
    """Return a filename-safe local timestamp."""
    return (moment or datetime.now().astimezone()).strftime("%Y%m%d_%H%M%S")


def build_export_filename(
    prefix: str, extension: str, moment: datetime | None = None
) -> str:
    """Build a safe timestamped export filename."""
    safe_prefix = re.sub(r"[^A-Za-z0-9_-]+", "_", prefix.strip()).strip("_")
    safe_extension = extension.strip().lstrip(".").lower()
    if not safe_prefix:
        raise ValueError("Export filename prefix cannot be empty.")
    if not safe_extension or not safe_extension.isalnum():
        raise ValueError("Export extension must contain only letters or numbers.")
    return f"{safe_prefix}_{build_timestamp(moment)}.{safe_extension}"


def save_text_report(content: str, output_dir: str | Path, filename: str) -> Path:
    """Save a UTF-8 Markdown or HTML report and return the absolute path."""
    directory = ensure_output_dir(output_dir)
    destination = directory / Path(filename).name
    destination.write_text(content, encoding="utf-8", newline="\n")
    return destination


def save_analysis_csv(
    dataframe: pd.DataFrame, output_dir: str | Path, filename: str
) -> Path:
    """Save a UTF-8-sig CSV so Chinese text opens correctly in Excel."""
    directory = ensure_output_dir(output_dir)
    destination = directory / Path(filename).name
    dataframe.to_csv(destination, index=False, encoding="utf-8-sig")
    return destination

