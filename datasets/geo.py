# datasets/geo.py

"""
GEO dataset utilities.

Gene Expression Omnibus (GEO) dataset handling for the doctoral project.

Responsibilities
----------------
- Represent a GEO dataset.
- Validate GEO accession identifiers.
- Build GEO download URLs.
- Download GEO supplementary files.
- Download GEO series matrix files when available.
- Store raw GEO data under data/raw/rna/.
- Provide basic dataset metadata.
- Avoid performing biological analysis.

Expected project structure
--------------------------
Doktorat_Kod/
├── data/
│   └── raw/
│       └── rna/
│           ├── GSE130973/
│           ├── GSE281449/
│           └── GSE226189/
│
├── datasets/
│   └── geo.py
│
├── pipeline/
│   └── rna_pipeline.py
│
└── analysis/
    └── rna_analysis.py

GEO:
    https://www.ncbi.nlm.nih.gov/geo/

This module uses only public GEO data.
"""

from __future__ import annotations

import gzip
import json
import logging
import re
import shutil
import tarfile
import zipfile

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

NCBI_GEO_BASE_URL = "https://www.ncbi.nlm.nih.gov/geo"

GEO_SERIES_URL = (
    f"{NCBI_GEO_BASE_URL}/query/acc.cgi"
    "?db=gds&acc={accession}&form=text&view=quick"
)

GEO_SUPPLEMENTARY_URL = (
    f"{NCBI_GEO_BASE_URL}/data/supplementary/series/"
    "{prefix}/{accession}_suppl.tar"
)

DEFAULT_USER_AGENT = (
    "Doktorat_Kod/1.0 "
    "(research dataset downloader; GEO/NCBI)"
)

DEFAULT_CHUNK_SIZE = 1024 * 1024


# ---------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------


class GEOError(Exception):
    """Base exception for GEO-related errors."""


class InvalidGEOAccessionError(GEOError):
    """Raised when a GEO accession is invalid."""


class GEODownloadError(GEOError):
    """Raised when a GEO file cannot be downloaded."""


class GEOExtractionError(GEOError):
    """Raised when a GEO archive cannot be extracted."""


# ---------------------------------------------------------------------
# GEO dataset representation
# ---------------------------------------------------------------------


@dataclass
class GEODataset:
    """
    Representation of a GEO Series dataset.

    Example
    -------
    GEODataset(
        accession="GSE130973",
        title="Example dataset",
        description="Skin RNA dataset",
        organism="Homo sapiens",
    )
    """

    accession: str

    title: str = ""

    description: str = ""

    organism: str = "Homo sapiens"

    source: str = "NCBI GEO"

    modality: str = "RNA"

    local_path: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        self.accession = normalize_accession(self.accession)

        if self.metadata is None:
            self.metadata = {}

    @property
    def is_local(self) -> bool:
        """Return True if the dataset has a local path."""

        if self.local_path is None:
            return False

        return Path(self.local_path).exists()

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataset metadata to a dictionary."""

        return asdict(self)


# ---------------------------------------------------------------------
# Accession handling
# ---------------------------------------------------------------------


GEO_ACCESSION_PATTERN = re.compile(
    r"^GSE\d+$",
    re.IGNORECASE,
)


def normalize_accession(accession: str) -> str:
    """
    Normalize a GEO accession.

    Parameters
    ----------
    accession:
        GEO accession such as GSE130973.

    Returns
    -------
    str
        Normalized accession.

    Raises
    ------
    InvalidGEOAccessionError
        If accession does not match GSE<number>.
    """

    if not isinstance(accession, str):
        raise InvalidGEOAccessionError(
            "GEO accession must be a string."
        )

    accession = accession.strip().upper()

    if not GEO_ACCESSION_PATTERN.match(accession):
        raise InvalidGEOAccessionError(
            f"Invalid GEO accession: {accession!r}. "
            "Expected format such as GSE130973."
        )

    return accession


def validate_accession(accession: str) -> bool:
    """
    Check whether a GEO accession is valid.

    This checks the identifier format only.
    It does not verify that the dataset exists on NCBI.
    """

    try:
        normalize_accession(accession)
        return True
    except InvalidGEOAccessionError:
        return False


# ---------------------------------------------------------------------
# GEO URL construction
# ---------------------------------------------------------------------


def _geo_numeric_id(accession: str) -> str:
    """
    Extract numeric part from GSE accession.

    Example
    -------
    GSE130973 -> 130973
    """

    accession = normalize_accession(accession)

    return accession[3:]


def build_series_url(accession: str) -> str:
    """
    Build NCBI GEO quick-view URL.
    """

    accession = normalize_accession(accession)

    return GEO_SERIES_URL.format(
        accession=accession
    )


def build_supplementary_url(accession: str) -> str:
    """
    Build GEO supplementary TAR URL.

    GEO stores supplementary series files in
    directories grouped by accession number.

    Example:
        GSE130973
        -> 130000/GSE130973_suppl.tar
    """

    accession = normalize_accession(accession)

    numeric_id = _geo_numeric_id(accession)

    prefix = numeric_id[:-3] + "nnn"

    return GEO_SUPPLEMENTARY_URL.format(
        prefix=prefix,
        accession=accession,
    )


def build_matrix_url(accession: str) -> str:
    """
    Build GEO Series Matrix FTP/HTTP URL.

    GEO uses grouped accession directories.

    Example:
        GSE130973
        -> GSE130nnn/
    """

    accession = normalize_accession(accession)

    numeric_id = _geo_numeric_id(accession)

    prefix = numeric_id[:-3] + "nnn"

    filename = (
        f"{accession}_series_matrix.txt.gz"
    )

    return (
        f"{NCBI_GEO_BASE_URL}/matrix/"
        f"{prefix}/{accession}/"
        f"{filename}"
    )


# ---------------------------------------------------------------------
# Local dataset paths
# ---------------------------------------------------------------------


def get_geo_root(
    project_root: Optional[Path] = None,
) -> Path:
    """
    Return the root directory for raw GEO datasets.

    Default:
        ./data/raw/rna
    """

    if project_root is None:
        project_root = Path.cwd()

    return (
        Path(project_root)
        / "data"
        / "raw"
        / "rna"
    )


def get_dataset_path(
    accession: str,
    project_root: Optional[Path] = None,
) -> Path:
    """
    Return local directory for a GEO dataset.

    Example:
        data/raw/rna/GSE130973/
    """

    accession = normalize_accession(accession)

    return get_geo_root(project_root) / accession


def prepare_dataset_directory(
    accession: str,
    project_root: Optional[Path] = None,
) -> Path:
    """
    Create and return the local GEO dataset directory.
    """

    path = get_dataset_path(
        accession=accession,
        project_root=project_root,
    )

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


# ---------------------------------------------------------------------
# HTTP download
# ---------------------------------------------------------------------


def download_file(
    url: str,
    destination: Path,
    overwrite: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    timeout: int = 60,
) -> Path:
    """
    Download a file using urllib.

    Parameters
    ----------
    url:
        Source URL.

    destination:
        Local destination.

    overwrite:
        Whether an existing file should be replaced.

    chunk_size:
        Download chunk size.

    timeout:
        HTTP timeout in seconds.

    Returns
    -------
    Path
        Downloaded file path.
    """

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if destination.exists() and not overwrite:
        logger.info(
            "File already exists: %s",
            destination,
        )

        return destination

    request = Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
        },
    )

    temporary_path = destination.with_suffix(
        destination.suffix + ".part"
    )

    try:

        logger.info(
            "Downloading: %s",
            url,
        )

        with urlopen(
            request,
            timeout=timeout,
        ) as response:

            with open(
                temporary_path,
                "wb",
            ) as output:

                while True:

                    chunk = response.read(
                        chunk_size
                    )

                    if not chunk:
                        break

                    output.write(chunk)

        temporary_path.replace(destination)

        logger.info(
            "Downloaded: %s",
            destination,
        )

        return destination

    except (
        HTTPError,
        URLError,
        OSError,
    ) as exc:

        if temporary_path.exists():
            temporary_path.unlink()

        raise GEODownloadError(
            f"Could not download {url}: {exc}"
        ) from exc


# ---------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------


def fetch_series_metadata(
    accession: str,
    timeout: int = 60,
) -> str:
    """
    Download GEO quick-view metadata as text.

    Returns
    -------
    str
        Raw GEO metadata text.
    """

    accession = normalize_accession(accession)

    url = build_series_url(accession)

    request = Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
        },
    )

    try:

        with urlopen(
            request,
            timeout=timeout,
        ) as response:

            content = response.read()

        return content.decode(
            "utf-8",
            errors="replace",
        )

    except (
        HTTPError,
        URLError,
        OSError,
    ) as exc:

        raise GEODownloadError(
            f"Could not retrieve GEO metadata "
            f"for {accession}: {exc}"
        ) from exc


def save_metadata(
    accession: str,
    project_root: Optional[Path] = None,
    overwrite: bool = False,
) -> Path:
    """
    Download and save GEO metadata.

    Output:
        data/raw/rna/GSEXXXXX/GSEXXXXX_metadata.txt
    """

    accession = normalize_accession(accession)

    dataset_dir = prepare_dataset_directory(
        accession,
        project_root,
    )

    destination = (
        dataset_dir
        / f"{accession}_metadata.txt"
    )

    if destination.exists() and not overwrite:
        return destination

    metadata = fetch_series_metadata(
        accession
    )

    destination.write_text(
        metadata,
        encoding="utf-8",
    )

    return destination


# ---------------------------------------------------------------------
# Series Matrix
# ---------------------------------------------------------------------


def download_series_matrix(
    accession: str,
    project_root: Optional[Path] = None,
    overwrite: bool = False,
) -> Optional[Path]:
    """
    Download GEO Series Matrix file.

    The matrix file is useful for datasets where
    GEO provides processed expression data.

    Returns
    -------
    Path or None
        Downloaded matrix path.

    Notes
    -----
    Not every GEO dataset provides a usable series matrix.
    """

    accession = normalize_accession(accession)

    dataset_dir = prepare_dataset_directory(
        accession,
        project_root,
    )

    filename = (
        f"{accession}_series_matrix.txt.gz"
    )

    destination = dataset_dir / filename

    url = build_matrix_url(accession)

    try:

        return download_file(
            url=url,
            destination=destination,
            overwrite=overwrite,
        )

    except GEODownloadError as exc:

        logger.warning(
            "Series matrix unavailable for %s: %s",
            accession,
            exc,
        )

        return None


# ---------------------------------------------------------------------
# Supplementary files
# ---------------------------------------------------------------------


def download_supplementary_archive(
    accession: str,
    project_root: Optional[Path] = None,
    overwrite: bool = False,
) -> Optional[Path]:
    """
    Download GEO supplementary TAR archive.

    Example:
        GSE130973_suppl.tar
    """

    accession = normalize_accession(accession)

    dataset_dir = prepare_dataset_directory(
        accession,
        project_root,
    )

    filename = (
        f"{accession}_suppl.tar"
    )

    destination = dataset_dir / filename

    url = build_supplementary_url(
        accession
    )

    try:

        return download_file(
            url=url,
            destination=destination,
            overwrite=overwrite,
        )

    except GEODownloadError as exc:

        logger.warning(
            "Supplementary archive unavailable "
            "for %s: %s",
            accession,
            exc,
        )

        return None


# ---------------------------------------------------------------------
# Archive extraction
# ---------------------------------------------------------------------


def extract_tar(
    archive_path: Path,
    destination: Optional[Path] = None,
    overwrite: bool = False,
) -> List[Path]:
    """
    Extract a TAR archive.

    Returns
    -------
    list[Path]
        Extracted files.
    """

    archive_path = Path(archive_path)

    if not archive_path.exists():
        raise GEOExtractionError(
            f"Archive does not exist: "
            f"{archive_path}"
        )

    if destination is None:
        destination = archive_path.parent

    destination = Path(destination)

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    extracted_files: List[Path] = []

    try:

        with tarfile.open(
            archive_path,
            "r",
        ) as archive:

            members = archive.getmembers()

            for member in members:

                target = (
                    destination
                    / member.name
                )

                if target.exists() and not overwrite:
                    extracted_files.append(
                        target
                    )
                    continue

                archive.extract(
                    member,
                    destination,
                )

                extracted_files.append(
                    target
                )

    except (
        tarfile.TarError,
        OSError,
    ) as exc:

        raise GEOExtractionError(
            f"Could not extract {archive_path}: "
            f"{exc}"
        ) from exc

    return extracted_files


def extract_zip(
    archive_path: Path,
    destination: Optional[Path] = None,
    overwrite: bool = False,
) -> List[Path]:
    """
    Extract a ZIP archive.
    """

    archive_path = Path(archive_path)

    if not archive_path.exists():
        raise GEOExtractionError(
            f"Archive does not exist: "
            f"{archive_path}"
        )

    if destination is None:
        destination = archive_path.parent

    destination = Path(destination)

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    extracted_files: List[Path] = []

    try:

        with zipfile.ZipFile(
            archive_path,
            "r",
        ) as archive:

            for name in archive.namelist():

                target = (
                    destination
                    / name
                )

                if (
                    target.exists()
                    and not overwrite
                ):
                    extracted_files.append(
                        target
                    )
                    continue

                archive.extract(
                    name,
                    destination,
                )

                extracted_files.append(
                    target
                )

    except (
        zipfile.BadZipFile,
        OSError,
    ) as exc:

        raise GEOExtractionError(
            f"Could not extract {archive_path}: "
            f"{exc}"
        ) from exc

    return extracted_files


# ---------------------------------------------------------------------
# GZIP utilities
# ---------------------------------------------------------------------


def decompress_gzip(
    source: Path,
    destination: Optional[Path] = None,
    overwrite: bool = False,
) -> Path:
    """
    Decompress a .gz file.
    """

    source = Path(source)

    if not source.exists():
        raise FileNotFoundError(
            source
        )

    if destination is None:

        if source.suffix == ".gz":
            destination = source.with_suffix("")

        else:
            destination = Path(
                str(source) + ".decompressed"
            )

    destination = Path(destination)

    if destination.exists() and not overwrite:
        return destination

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with gzip.open(
        source,
        "rb",
    ) as input_file:

        with open(
            destination,
            "wb",
        ) as output_file:

            shutil.copyfileobj(
                input_file,
                output_file,
            )

    return destination


# ---------------------------------------------------------------------
# Dataset inventory
# ---------------------------------------------------------------------


def list_local_files(
    accession: str,
    project_root: Optional[Path] = None,
) -> List[Path]:
    """
    List all files stored for a GEO dataset.
    """

    dataset_dir = get_dataset_path(
        accession,
        project_root,
    )

    if not dataset_dir.exists():
        return []

    return sorted(
        path
        for path in dataset_dir.rglob("*")
        if path.is_file()
    )


def build_dataset_inventory(
    accession: str,
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Build a simple inventory of a local GEO dataset.
    """

    accession = normalize_accession(
        accession
    )

    dataset_dir = get_dataset_path(
        accession,
        project_root,
    )

    files = list_local_files(
        accession,
        project_root,
    )

    total_size = sum(
        file.stat().st_size
        for file in files
        if file.exists()
    )

    return {
        "accession": accession,
        "path": str(dataset_dir),
        "exists": dataset_dir.exists(),
        "num_files": len(files),
        "total_size_bytes": total_size,
        "files": [
            str(file)
            for file in files
        ],
    }


def save_inventory(
    accession: str,
    project_root: Optional[Path] = None,
) -> Path:
    """
    Save GEO dataset inventory as JSON.
    """

    accession = normalize_accession(
        accession
    )

    dataset_dir = prepare_dataset_directory(
        accession,
        project_root,
    )

    inventory = build_dataset_inventory(
        accession,
        project_root,
    )

    destination = (
        dataset_dir
        / "inventory.json"
    )

    destination.write_text(
        json.dumps(
            inventory,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return destination


# ---------------------------------------------------------------------
# Dataset preparation
# ---------------------------------------------------------------------


def prepare_geo_dataset(
    accession: str,
    project_root: Optional[Path] = None,
    download_metadata: bool = True,
    download_matrix: bool = False,
    download_supplementary: bool = False,
    extract_supplementary: bool = False,
) -> GEODataset:
    """
    Prepare a GEO dataset locally.

    Parameters
    ----------
    accession:
        GEO Series accession.

    project_root:
        Root of Doktorat_Kod project.

    download_metadata:
        Download GEO metadata.

    download_matrix:
        Attempt to download series matrix.

    download_supplementary:
        Attempt to download supplementary TAR.

    extract_supplementary:
        Extract supplementary TAR after download.

    Returns
    -------
    GEODataset
        Dataset description.

    Important
    ---------
    For large datasets, supplementary downloads may be very large.
    Keep download_supplementary=False unless the specific dataset
    requires supplementary files.
    """

    accession = normalize_accession(
        accession
    )

    dataset_dir = prepare_dataset_directory(
        accession,
        project_root,
    )

    dataset = GEODataset(
        accession=accession,
        local_path=str(dataset_dir),
    )

    if download_metadata:

        try:

            metadata_path = save_metadata(
                accession,
                project_root,
            )

            dataset.metadata[
                "metadata_file"
            ] = str(metadata_path)

        except GEODownloadError as exc:

            logger.warning(
                "Metadata download failed: %s",
                exc,
            )

    if download_matrix:

        matrix_path = download_series_matrix(
            accession,
            project_root,
        )

        if matrix_path is not None:

            dataset.metadata[
                "series_matrix"
            ] = str(matrix_path)

    if download_supplementary:

        archive_path = (
            download_supplementary_archive(
                accession,
                project_root,
            )
        )

        if archive_path is not None:

            dataset.metadata[
                "supplementary_archive"
            ] = str(archive_path)

            if extract_supplementary:

                extracted = extract_tar(
                    archive_path
                )

                dataset.metadata[
                    "supplementary_files"
                ] = [
                    str(path)
                    for path in extracted
                ]

    inventory_path = save_inventory(
        accession,
        project_root,
    )

    dataset.metadata[
        "inventory"
    ] = str(inventory_path)

    return dataset


# ---------------------------------------------------------------------
# Project datasets
# ---------------------------------------------------------------------


PROJECT_GEO_DATASETS = (
    "GSE130973",
    "GSE281449",
    "GSE226189",
)


def get_project_geo_datasets() -> List[GEODataset]:
    """
    Return the GEO datasets currently registered
    for the project.
    """

    return [
        GEODataset(
            accession=accession
        )
        for accession
        in PROJECT_GEO_DATASETS
    ]


def prepare_project_geo_directories(
    project_root: Optional[Path] = None,
) -> List[Path]:
    """
    Create directories for all registered GEO datasets.

    This does NOT download the datasets.
    """

    directories = []

    for accession in PROJECT_GEO_DATASETS:

        directories.append(
            prepare_dataset_directory(
                accession,
                project_root,
            )
        )

    return directories


# ---------------------------------------------------------------------
# Dataset summary
# ---------------------------------------------------------------------


def summarize_geo_dataset(
    accession: str,
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Return a compact summary of a local GEO dataset.
    """

    accession = normalize_accession(
        accession
    )

    inventory = build_dataset_inventory(
        accession,
        project_root,
    )

    return {
        "accession": accession,
        "local_path": inventory["path"],
        "exists": inventory["exists"],
        "num_files": inventory["num_files"],
        "size_mb": round(
            inventory["total_size_bytes"]
            / (1024 ** 2),
            2,
        ),
    }


# ---------------------------------------------------------------------
# Example / smoke test
# ---------------------------------------------------------------------


def main() -> None:
    """
    Basic module test.

    This does not download large datasets.
    """

    print("# GEO Dataset Manager")

    print()

    print(
        "Registered project GEO datasets:"
    )

    for dataset in get_project_geo_datasets():

        print(
            f"  - {dataset.accession}"
        )

    print()

    print(
        "Example local directories:"
    )

    for path in prepare_project_geo_directories():

        print(
            f"  - {path}"
        )

    print()

    accession = "GSE130973"

    print(
        f"Accession validation: "
        f"{validate_accession(accession)}"
    )

    print(
        f"Series URL: "
        f"{build_series_url(accession)}"
    )

    print(
        f"Supplementary URL: "
        f"{build_supplementary_url(accession)}"
    )

    print(
        f"Matrix URL: "
        f"{build_matrix_url(accession)}"
    )

    print()

    print("GEO module ready.")


if __name__ == "__main__":
    main()