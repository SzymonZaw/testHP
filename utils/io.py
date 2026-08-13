# utils/io.py

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Optional

import numpy as np


def ensure_dir(
    path: str | Path,
) -> Path:
    """
    Create directory if it does not exist.
    """

    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    return path


def save_json(
    data: Any,
    path: str | Path,
    indent: int = 2,
) -> Path:
    """
    Save Python object as JSON.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=indent,
            ensure_ascii=False,
        )

    return path


def load_json(
    path: str | Path,
) -> Any:
    """
    Load JSON file.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def save_yaml(
    data: Any,
    path: str | Path,
) -> Path:
    """
    Save Python object as YAML.
    """

    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required for YAML support."
        ) from exc

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True,
        )

    return path


def load_yaml(
    path: str | Path,
) -> Any:
    """
    Load YAML file.
    """

    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required for YAML support."
        ) from exc

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        return yaml.safe_load(f)


def save_numpy(
    array: np.ndarray,
    path: str | Path,
) -> Path:
    """
    Save NumPy array.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    np.save(path, array)

    return path


def load_numpy(
    path: str | Path,
) -> np.ndarray:
    """
    Load NumPy array.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    return np.load(path)


def save_npz(
    path: str | Path,
    **arrays: np.ndarray,
) -> Path:
    """
    Save multiple NumPy arrays into NPZ archive.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        path,
        **arrays,
    )

    return path


def load_npz(
    path: str | Path,
) -> dict[str, np.ndarray]:
    """
    Load NPZ archive into dictionary.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    data = np.load(path)

    return {
        key: data[key]
        for key in data.files
    }


def save_csv(
    rows: Iterable[dict[str, Any]],
    path: str | Path,
    fieldnames: Optional[list[str]] = None,
) -> Path:
    """
    Save iterable of dictionaries to CSV.
    """

    rows = list(rows)

    if not rows:
        raise ValueError(
            "Cannot save empty CSV without fieldnames."
        )

    if fieldnames is None:
        fieldnames = list(rows[0].keys())

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    return path


def load_csv(
    path: str | Path,
) -> list[dict[str, str]]:
    """
    Load CSV into a list of dictionaries.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    with open(
        path,
        "r",
        newline="",
        encoding="utf-8",
    ) as f:

        reader = csv.DictReader(f)

        return list(reader)


def list_files(
    root: str | Path,
    extensions: Optional[Iterable[str]] = None,
    recursive: bool = True,
) -> list[Path]:
    """
    List files under a directory.

    Parameters
    ----------
    root:
        Directory to search.
    extensions:
        Optional file extensions, e.g. [".png", ".jpg"].
    recursive:
        Whether to search recursively.
    """

    root = Path(root)

    if not root.exists():
        return []

    if extensions is not None:
        normalized = {
            ext.lower()
            if ext.startswith(".")
            else f".{ext.lower()}"
            for ext in extensions
        }
    else:
        normalized = None

    iterator = root.rglob("*") if recursive else root.glob("*")

    files = []

    for path in iterator:
        if not path.is_file():
            continue

        if normalized is not None:
            if path.suffix.lower() not in normalized:
                continue

        files.append(path)

    return sorted(files)


def file_exists(
    path: str | Path,
) -> bool:
    """
    Check whether a file exists.
    """

    return Path(path).is_file()


def directory_exists(
    path: str | Path,
) -> bool:
    """
    Check whether a directory exists.
    """

    return Path(path).is_dir()