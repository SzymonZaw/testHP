"""
dinov2_model.py

Wrapper dla modeli DINOv2 używanych do ekstrakcji reprezentacji obrazów
skóry/tkanek.

Odpowiedzialności:
- ładowanie modelu DINOv2,
- preprocessing obrazów,
- ekstrakcja embeddingów,
- batch inference,
- opcjonalna normalizacja embeddingów,
- podobieństwo cosine,
- zapis/odczyt embeddingów.

Model nie wykonuje:
- segmentacji,
- klasyfikacji patologii,
- treningu modeli końcowych,
- fuzji multimodalnej.

Te zadania powinny znajdować się odpowiednio w:
    sam2_model.py
    cellpose_model.py
    pathology_model.py
    fusion_model.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image


PathLike = Union[str, Path]


# ============================================================
# Configuration
# ============================================================

@dataclass
class DINOv2Config:
    """
    Konfiguracja modelu DINOv2.
    """

    model_name: str = "dinov2_vitb14"

    device: Optional[str] = None

    image_size: int = 224

    batch_size: int = 16

    normalize_embeddings: bool = True

    use_fp16: bool = True

    num_workers: int = 0


# ============================================================
# Model names
# ============================================================

SUPPORTED_MODELS = {
    "dinov2_vits14",
    "dinov2_vitb14",
    "dinov2_vitl14",
    "dinov2_vitg14",
}


# ============================================================
# Image normalization
# ============================================================

IMAGENET_MEAN = (
    0.485,
    0.456,
    0.406,
)

IMAGENET_STD = (
    0.229,
    0.224,
    0.225,
)


# ============================================================
# DINOv2 Model
# ============================================================

class DINOv2Model(nn.Module):
    """
    Wrapper dla DINOv2.

    Przykład:

        model = DINOv2Model()

        embedding = model.encode_image(
            "data/raw/images/lesions/example.jpg"
        )

    Wynik:
        tensor [embedding_dim]

    Batch:

        embeddings = model.encode_images(
            [
                "image1.jpg",
                "image2.jpg",
                "image3.jpg",
            ]
        )
    """

    def __init__(
        self,
        config: Optional[DINOv2Config] = None,
    ) -> None:

        super().__init__()

        self.config = config or DINOv2Config()

        self.device = self._resolve_device(
            self.config.device
        )

        self.model = self._load_model(
            self.config.model_name
        )

        self.model.eval()

        self.transform = self._build_transform()

        self.embedding_dim = self._get_embedding_dim()

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    @staticmethod
    def _resolve_device(
        device: Optional[str],
    ) -> torch.device:

        if device is not None:
            return torch.device(device)

        if torch.cuda.is_available():
            return torch.device("cuda")

        if hasattr(torch.backends, "mps"):
            if torch.backends.mps.is_available():
                return torch.device("mps")

        return torch.device("cpu")

    # --------------------------------------------------------
    # Model loading
    # --------------------------------------------------------

    def _load_model(
        self,
        model_name: str,
    ) -> nn.Module:

        if model_name not in SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported DINOv2 model: {model_name}. "
                f"Supported models: {sorted(SUPPORTED_MODELS)}"
            )

        try:
            model = torch.hub.load(
                "facebookresearch/dinov2",
                model_name,
            )

        except Exception as exc:
            raise RuntimeError(
                "Nie udało się załadować DINOv2.\n"
                "Przy pierwszym uruchomieniu wymagane jest "
                "pobranie modelu z repozytorium "
                "facebookresearch/dinov2.\n\n"
                f"Original error: {exc}"
            ) from exc

        model = model.to(self.device)

        return model

    # --------------------------------------------------------
    # Image transform
    # --------------------------------------------------------

    def _build_transform(self):
        """
        Standardowy preprocessing ImageNet używany dla DINOv2.
        """

        try:
            from torchvision import transforms

        except ImportError as exc:
            raise ImportError(
                "torchvision jest wymagane dla DINOv2."
            ) from exc

        return transforms.Compose(
            [
                transforms.Resize(
                    (
                        self.config.image_size,
                        self.config.image_size,
                    )
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=IMAGENET_MEAN,
                    std=IMAGENET_STD,
                ),
            ]
        )

    # --------------------------------------------------------
    # Embedding dimension
    # --------------------------------------------------------

    def _get_embedding_dim(self) -> int:
        """
        Określa rozmiar embeddingu generowanego przez model.
        """

        dummy = torch.zeros(
            1,
            3,
            self.config.image_size,
            self.config.image_size,
            device=self.device,
        )

        with torch.no_grad():
            output = self.model(dummy)

        if output.ndim != 2:
            raise RuntimeError(
                f"Unexpected DINOv2 output shape: {output.shape}"
            )

        return int(output.shape[-1])

    # --------------------------------------------------------
    # Image loading
    # --------------------------------------------------------

    @staticmethod
    def _load_image(
        image: Union[Image.Image, PathLike],
    ) -> Image.Image:

        if isinstance(image, Image.Image):
            return image.convert("RGB")

        path = Path(image)

        if not path.exists():
            raise FileNotFoundError(
                f"Image not found: {path}"
            )

        try:
            return Image.open(path).convert("RGB")

        except Exception as exc:
            raise RuntimeError(
                f"Could not read image: {path}"
            ) from exc

    # --------------------------------------------------------
    # Prepare image
    # --------------------------------------------------------

    def _prepare_image(
        self,
        image: Union[Image.Image, PathLike],
    ) -> torch.Tensor:

        image = self._load_image(image)

        tensor = self.transform(image)

        return tensor

    # --------------------------------------------------------
    # Encode batch
    # --------------------------------------------------------

    @torch.no_grad()
    def encode_batch(
        self,
        images: Sequence[
            Union[Image.Image, PathLike]
        ],
    ) -> torch.Tensor:
        """
        Generuje embeddingi dla batcha obrazów.

        Parameters
        ----------
        images:
            Lista ścieżek lub PIL.Image.

        Returns
        -------
        torch.Tensor
            Tensor [N, embedding_dim].
        """

        if len(images) == 0:
            return torch.empty(
                0,
                self.embedding_dim,
                device=self.device,
            )

        tensors = [
            self._prepare_image(image)
            for image in images
        ]

        batch = torch.stack(tensors).to(
            self.device,
            non_blocking=True,
        )

        use_amp = (
            self.config.use_fp16
            and self.device.type == "cuda"
        )

        if use_amp:
            with torch.autocast(
                device_type="cuda",
                dtype=torch.float16,
            ):
                embeddings = self.model(batch)

        else:
            embeddings = self.model(batch)

        embeddings = embeddings.float()

        if self.config.normalize_embeddings:
            embeddings = F.normalize(
                embeddings,
                p=2,
                dim=-1,
            )

        return embeddings

    # --------------------------------------------------------
    # Encode single image
    # --------------------------------------------------------

    @torch.no_grad()
    def encode_image(
        self,
        image: Union[Image.Image, PathLike],
    ) -> torch.Tensor:
        """
        Generuje embedding dla pojedynczego obrazu.

        Returns
        -------
        torch.Tensor
            Tensor [embedding_dim].
        """

        embeddings = self.encode_batch(
            [image]
        )

        return embeddings[0]

    # --------------------------------------------------------
    # Encode many images
    # --------------------------------------------------------

    @torch.no_grad()
    def encode_images(
        self,
        images: Sequence[
            Union[Image.Image, PathLike]
        ],
        batch_size: Optional[int] = None,
    ) -> torch.Tensor:
        """
        Generuje embeddingi dla dużego zbioru obrazów.

        Obrazy są automatycznie dzielone na batch'e,
        aby ograniczyć zużycie VRAM.

        Returns
        -------
        torch.Tensor
            Tensor [N, embedding_dim].
        """

        if batch_size is None:
            batch_size = self.config.batch_size

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        all_embeddings = []

        for start in range(
            0,
            len(images),
            batch_size,
        ):

            end = min(
                start + batch_size,
                len(images),
            )

            batch_images = images[start:end]

            embeddings = self.encode_batch(
                batch_images
            )

            all_embeddings.append(
                embeddings.cpu()
            )

        if not all_embeddings:
            return torch.empty(
                0,
                self.embedding_dim,
            )

        return torch.cat(
            all_embeddings,
            dim=0,
        )

    # --------------------------------------------------------
    # Directory encoding
    # --------------------------------------------------------

    def encode_directory(
        self,
        directory: PathLike,
        extensions: Optional[Iterable[str]] = None,
        batch_size: Optional[int] = None,
    ) -> tuple[torch.Tensor, List[str]]:
        """
        Generuje embeddingi dla wszystkich obrazów
        znajdujących się w katalogu.

        Parameters
        ----------
        directory:
            Katalog z obrazami.

        extensions:
            Rozszerzenia, np.
            [".jpg", ".jpeg", ".png"].

        Returns
        -------
        embeddings:
            Tensor [N, embedding_dim]

        paths:
            Lista ścieżek odpowiadających embeddingom.
        """

        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(
                f"Directory not found: {directory}"
            )

        if extensions is None:
            extensions = (
                ".jpg",
                ".jpeg",
                ".png",
                ".bmp",
                ".tif",
                ".tiff",
                ".webp",
            )

        extensions = {
            ext.lower()
            for ext in extensions
        }

        image_paths = sorted(
            str(path)
            for path in directory.rglob("*")
            if path.is_file()
            and path.suffix.lower() in extensions
        )

        embeddings = self.encode_images(
            image_paths,
            batch_size=batch_size,
        )

        return embeddings, image_paths

    # --------------------------------------------------------
    # Save embeddings
    # --------------------------------------------------------

    @staticmethod
    def save_embeddings(
        embeddings: torch.Tensor,
        paths: Sequence[str],
        output_path: PathLike,
    ) -> None:
        """
        Zapisuje embeddingi wraz z odpowiadającymi ścieżkami.

        Format:
            .npz

        Zawiera:
            embeddings
            paths
        """

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        embeddings_np = (
            embeddings.detach()
            .cpu()
            .numpy()
        )

        paths_np = np.asarray(
            paths,
            dtype=str,
        )

        np.savez_compressed(
            output_path,
            embeddings=embeddings_np,
            paths=paths_np,
        )

    # --------------------------------------------------------
    # Load embeddings
    # --------------------------------------------------------

    @staticmethod
    def load_embeddings(
        input_path: PathLike,
    ) -> tuple[torch.Tensor, List[str]]:
        """
        Wczytuje wcześniej zapisane embeddingi.
        """

        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Embedding file not found: {input_path}"
            )

        data = np.load(
            input_path,
            allow_pickle=False,
        )

        embeddings = torch.from_numpy(
            data["embeddings"]
        )

        paths = data["paths"].tolist()

        return embeddings, paths

    # --------------------------------------------------------
    # Cosine similarity
    # --------------------------------------------------------

    @staticmethod
    def cosine_similarity(
        embedding_a: torch.Tensor,
        embedding_b: torch.Tensor,
    ) -> torch.Tensor:
        """
        Oblicza cosine similarity.

        Obsługiwane:
            [D] x [D]
            [N,D] x [D]
            [N,D] x [N,D]
        """

        a = F.normalize(
            embedding_a.float(),
            p=2,
            dim=-1,
        )

        b = F.normalize(
            embedding_b.float(),
            p=2,
            dim=-1,
        )

        return torch.matmul(
            a,
            b.transpose(-1, -2),
        )

    # --------------------------------------------------------
    # Nearest neighbors
    # --------------------------------------------------------

    @staticmethod
    def nearest_neighbors(
        query_embedding: torch.Tensor,
        database_embeddings: torch.Tensor,
        k: int = 5,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Znajduje najbardziej podobne embeddingi.

        Returns
        -------
        scores:
            cosine similarity

        indices:
            indeksy najbardziej podobnych obrazów
        """

        if k <= 0:
            raise ValueError(
                "k must be greater than 0."
            )

        if database_embeddings.ndim != 2:
            raise ValueError(
                "database_embeddings must have shape [N, D]."
            )

        query = F.normalize(
            query_embedding.float(),
            p=2,
            dim=-1,
        )

        database = F.normalize(
            database_embeddings.float(),
            p=2,
            dim=-1,
        )

        scores = torch.matmul(
            database,
            query,
        )

        k = min(
            k,
            database.shape[0],
        )

        values, indices = torch.topk(
            scores,
            k=k,
        )

        return values, indices


# ============================================================
# Utility functions
# ============================================================

def load_dinov2(
    model_name: str = "dinov2_vitb14",
    device: Optional[str] = None,
) -> DINOv2Model:
    """
    Skrócony konstruktor modelu.
    """

    config = DINOv2Config(
        model_name=model_name,
        device=device,
    )

    return DINOv2Model(config)


def extract_embeddings(
    image_paths: Sequence[PathLike],
    output_path: Optional[PathLike] = None,
    model_name: str = "dinov2_vitb14",
    batch_size: int = 16,
    device: Optional[str] = None,
) -> tuple[torch.Tensor, List[str]]:
    """
    Wygodna funkcja do ekstrakcji embeddingów.

    Przykład:

        embeddings, paths = extract_embeddings(
            image_paths,
            "data/processed/embeddings/lesions.npz",
        )
    """

    config = DINOv2Config(
        model_name=model_name,
        device=device,
        batch_size=batch_size,
    )

    model = DINOv2Model(config)

    embeddings = model.encode_images(
        image_paths,
        batch_size=batch_size,
    )

    paths = [
        str(path)
        for path in image_paths
    ]

    if output_path is not None:
        model.save_embeddings(
            embeddings,
            paths,
            output_path,
        )

    return embeddings, paths


# ============================================================
# Example
# ============================================================

if __name__ == "__main__":

    print("DINOv2 model test")

    config = DINOv2Config(
        model_name="dinov2_vitb14",
        batch_size=4,
    )

    model = DINOv2Model(config)

    print(f"Device: {model.device}")
    print(f"Model: {config.model_name}")
    print(f"Embedding dimension: {model.embedding_dim}")

    # --------------------------------------------------------
    # Example with a single image
    # --------------------------------------------------------
    #
    # image_path = (
    #     "data/raw/images/lesions/ISIC/example.jpg"
    # )
    #
    # embedding = model.encode_image(
    #     image_path
    # )
    #
    # print(
    #     "Embedding shape:",
    #     embedding.shape
    # )
    #
    # --------------------------------------------------------
    # Example with directory
    # --------------------------------------------------------
    #
    # embeddings, paths = model.encode_directory(
    #     "data/raw/images/lesions/ISIC"
    # )
    #
    # print(
    #     "Embeddings:",
    #     embeddings.shape
    # )
    #
    # model.save_embeddings(
    #     embeddings,
    #     paths,
    #     "data/processed/embeddings/"
    #     "isic_dinov2.npz",
    # )