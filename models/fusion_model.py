"""
fusion_model.py

Multimodal feature fusion for the doctoral project.

The module provides:
    - configuration dataclass
    - projection of modality-specific embeddings
    - several fusion strategies
    - optional modality dropout
    - missing-modality handling
    - attention-based multimodal fusion
    - a unified MultimodalFusionModel
    - utilities for inspecting modality availability

Expected input modalities may include:
    - image
    - cell
    - wsi
    - rna
    - hand

The model is intentionally independent from:
    - SAM2
    - Cellpose
    - DINOv2
    - Scanpy
    - MediaPipe / MANO
    - MONAI

Those models should produce embeddings/features which are passed
to this module.

Typical pipeline:

    image -> DINOv2 --------\
    cells -> Cellpose ------\
    WSI -> MONAI ------------> fusion_model -> downstream model
    RNA -> Scanpy ----------/
    hand -> MediaPipe/MANO -/

Example:

    fusion = MultimodalFusionModel(
        modality_dims={
            "image": 768,
            "cell": 256,
            "wsi": 512,
            "rna": 256,
            "hand": 128,
        },
        fusion_dim=512,
        fusion_type="attention",
    )

    output = fusion({
        "image": image_embedding,
        "cell": cell_embedding,
        "wsi": wsi_embedding,
        "rna": rna_embedding,
        "hand": hand_embedding,
    })

    fused_embedding = output["fused_embedding"]

Author:
    Doctoral project
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class FusionConfig:
    """
    Configuration for multimodal feature fusion.

    Parameters
    ----------
    fusion_dim:
        Common dimensionality to which all modalities are projected.

    hidden_dim:
        Hidden dimensionality used by the fusion network.

    output_dim:
        Final dimensionality of the fused representation.

    dropout:
        Standard dropout probability.

    modality_dropout:
        Probability of randomly dropping a modality during training.

    fusion_type:
        Fusion strategy:
            - "concat"
            - "mean"
            - "sum"
            - "attention"
            - "gated"

    normalize:
        Whether to L2-normalize the final fused embedding.

    use_modality_embeddings:
        Whether each modality receives a learned modality embedding.
    """

    fusion_dim: int = 512
    hidden_dim: int = 512
    output_dim: int = 512

    dropout: float = 0.1
    modality_dropout: float = 0.0

    fusion_type: str = "attention"

    normalize: bool = True
    use_modality_embeddings: bool = True


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _validate_probability(value: float, name: str) -> None:
    """Validate a probability value."""
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def _ensure_2d(
    tensor: torch.Tensor,
    expected_dim: Optional[int] = None,
    name: str = "tensor",
) -> torch.Tensor:
    """
    Ensure a tensor has shape [batch, features].

    Accepts:
        [features]
        [batch, features]

    Returns:
        [batch, features]
    """

    if not isinstance(tensor, torch.Tensor):
        raise TypeError(
            f"{name} must be torch.Tensor, got {type(tensor).__name__}"
        )

    if tensor.ndim == 1:
        tensor = tensor.unsqueeze(0)

    if tensor.ndim != 2:
        raise ValueError(
            f"{name} must have shape [features] or [batch, features], "
            f"got {tuple(tensor.shape)}"
        )

    if expected_dim is not None and tensor.shape[-1] != expected_dim:
        raise ValueError(
            f"{name} expected feature dimension {expected_dim}, "
            f"got {tensor.shape[-1]}"
        )

    return tensor


def masked_mean(
    x: torch.Tensor,
    mask: torch.Tensor,
    dim: int,
) -> torch.Tensor:
    """
    Compute a masked mean.

    Parameters
    ----------
    x:
        Tensor to reduce.

    mask:
        Boolean mask broadcastable to x.

    dim:
        Dimension to reduce.
    """

    mask = mask.to(dtype=x.dtype)

    numerator = (x * mask).sum(dim=dim)
    denominator = mask.sum(dim=dim).clamp_min(1.0)

    return numerator / denominator


# ---------------------------------------------------------------------------
# Modality projection
# ---------------------------------------------------------------------------


class ModalityProjector(nn.Module):
    """
    Projects modality-specific embeddings into a common latent space.

    Example:

        image: 768 -> 512
        RNA:   256 -> 512
        hand:  128 -> 512

    All modalities therefore become compatible with the fusion module.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()

        if input_dim <= 0:
            raise ValueError("input_dim must be positive")

        if output_dim <= 0:
            raise ValueError("output_dim must be positive")

        _validate_probability(dropout, "dropout")

        self.input_dim = input_dim
        self.output_dim = output_dim

        self.network = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, output_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.LayerNorm(output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = _ensure_2d(
            x,
            expected_dim=self.input_dim,
            name="modality embedding",
        )

        return self.network(x)


# ---------------------------------------------------------------------------
# Attention fusion
# ---------------------------------------------------------------------------


class MultimodalAttentionFusion(nn.Module):
    """
    Attention-based fusion of modality embeddings.

    Input:
        [batch, num_modalities, fusion_dim]

    Output:
        [batch, fusion_dim]
    """

    def __init__(
        self,
        embedding_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()

        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")

        if num_heads <= 0:
            raise ValueError("num_heads must be positive")

        if embedding_dim % num_heads != 0:
            raise ValueError(
                f"embedding_dim ({embedding_dim}) must be divisible "
                f"by num_heads ({num_heads})"
            )

        self.embedding_dim = embedding_dim

        self.attention = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )

        self.norm1 = nn.LayerNorm(embedding_dim)

        self.ffn = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.Dropout(dropout),
        )

        self.norm2 = nn.LayerNorm(embedding_dim)

        self.attention_pool = nn.Linear(
            embedding_dim,
            1,
        )

    def forward(
        self,
        x: torch.Tensor,
        modality_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Parameters
        ----------
        x:
            [batch, modalities, embedding_dim]

        modality_mask:
            Boolean tensor:
                [batch, modalities]

            True means modality is available.

        Returns
        -------
        fused:
            [batch, embedding_dim]

        attention_weights:
            [batch, modalities]
        """

        if x.ndim != 3:
            raise ValueError(
                "Attention fusion expects [batch, modalities, embedding_dim]"
            )

        batch_size, num_modalities, dim = x.shape

        if dim != self.embedding_dim:
            raise ValueError(
                f"Expected embedding dimension {self.embedding_dim}, "
                f"got {dim}"
            )

        key_padding_mask = None

        if modality_mask is not None:

            if modality_mask.shape != (
                batch_size,
                num_modalities,
            ):
                raise ValueError(
                    "modality_mask must have shape "
                    f"[{batch_size}, {num_modalities}]"
                )

            # MultiheadAttention uses True to indicate positions
            # that should be ignored.
            key_padding_mask = ~modality_mask.bool()

        attended, _ = self.attention(
            x,
            x,
            x,
            key_padding_mask=key_padding_mask,
            need_weights=False,
        )

        x = self.norm1(x + attended)

        x = self.norm2(
            x + self.ffn(x)
        )

        # Attention pooling over modalities.
        scores = self.attention_pool(x).squeeze(-1)

        if modality_mask is not None:
            scores = scores.masked_fill(
                ~modality_mask.bool(),
                float("-inf"),
            )

        attention_weights = torch.softmax(
            scores,
            dim=-1,
        )

        # Handle pathological all-missing case.
        if modality_mask is not None:

            no_modalities = ~modality_mask.any(dim=-1)

            if no_modalities.any():

                attention_weights = attention_weights.clone()

                attention_weights[no_modalities] = (
                    1.0 / num_modalities
                )

        fused = torch.sum(
            x * attention_weights.unsqueeze(-1),
            dim=1,
        )

        return fused, attention_weights


# ---------------------------------------------------------------------------
# Gated fusion
# ---------------------------------------------------------------------------


class GatedFusion(nn.Module):
    """
    Learns a separate importance gate for every modality.

    Each modality gets:

        gate = sigmoid(MLP(modality_embedding))

    The gated embeddings are then aggregated.
    """

    def __init__(
        self,
        embedding_dim: int,
        num_modalities: int,
        hidden_dim: int,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()

        self.embedding_dim = embedding_dim
        self.num_modalities = num_modalities

        self.gate_network = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(
        self,
        x: torch.Tensor,
        modality_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Parameters
        ----------
        x:
            [batch, modalities, embedding_dim]

        modality_mask:
            [batch, modalities]

        Returns
        -------
        fused:
            [batch, embedding_dim]

        gates:
            [batch, modalities]
        """

        logits = self.gate_network(x).squeeze(-1)

        gates = torch.sigmoid(logits)

        if modality_mask is not None:

            gates = gates * modality_mask.float()

        denominator = gates.sum(
            dim=-1,
            keepdim=True,
        ).clamp_min(1e-6)

        weights = gates / denominator

        fused = torch.sum(
            x * weights.unsqueeze(-1),
            dim=1,
        )

        return fused, weights


# ---------------------------------------------------------------------------
# Main fusion model
# ---------------------------------------------------------------------------


class MultimodalFusionModel(nn.Module):
    """
    Main multimodal fusion model.

    Supported modalities are configurable.

    Example:

        modality_dims = {
            "image": 768,
            "cell": 256,
            "wsi": 512,
            "rna": 256,
            "hand": 128,
        }

    The model:

        modality embeddings
                |
                v
        modality projectors
                |
                v
        common latent space
                |
                v
        multimodal fusion
                |
                v
        fused embedding
    """

    DEFAULT_MODALITIES = (
        "image",
        "cell",
        "wsi",
        "rna",
        "hand",
    )

    def __init__(
        self,
        modality_dims: Mapping[str, int],
        fusion_dim: int = 512,
        hidden_dim: int = 512,
        output_dim: int = 512,
        fusion_type: str = "attention",
        dropout: float = 0.1,
        modality_dropout: float = 0.0,
        normalize: bool = True,
        use_modality_embeddings: bool = True,
        attention_heads: int = 8,
    ) -> None:
        super().__init__()

        if not modality_dims:
            raise ValueError(
                "modality_dims cannot be empty"
            )

        if fusion_type not in {
            "concat",
            "mean",
            "sum",
            "attention",
            "gated",
        }:
            raise ValueError(
                "fusion_type must be one of: "
                "'concat', 'mean', 'sum', 'attention', 'gated'"
            )

        _validate_probability(
            dropout,
            "dropout",
        )

        _validate_probability(
            modality_dropout,
            "modality_dropout",
        )

        self.modality_dims = dict(modality_dims)
        self.modalities = list(modality_dims.keys())

        self.fusion_dim = fusion_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.fusion_type = fusion_type
        self.normalize = normalize
        self.modality_dropout = modality_dropout
        self.use_modality_embeddings = (
            use_modality_embeddings
        )

        # ---------------------------------------------------------------
        # Projection layers
        # ---------------------------------------------------------------

        self.projectors = nn.ModuleDict()

        for modality, input_dim in self.modality_dims.items():

            self.projectors[modality] = ModalityProjector(
                input_dim=input_dim,
                output_dim=fusion_dim,
                dropout=dropout,
            )

        # ---------------------------------------------------------------
        # Modality embeddings
        # ---------------------------------------------------------------

        if use_modality_embeddings:

            self.modality_embeddings = nn.Parameter(
                torch.randn(
                    len(self.modalities),
                    fusion_dim,
                )
                * 0.02
            )

        else:

            self.register_parameter(
                "modality_embeddings",
                None,
            )

        # ---------------------------------------------------------------
        # Fusion modules
        # ---------------------------------------------------------------

        if fusion_type == "attention":

            self.fusion_module = MultimodalAttentionFusion(
                embedding_dim=fusion_dim,
                num_heads=attention_heads,
                dropout=dropout,
            )

        elif fusion_type == "gated":

            self.fusion_module = GatedFusion(
                embedding_dim=fusion_dim,
                num_modalities=len(self.modalities),
                hidden_dim=hidden_dim,
                dropout=dropout,
            )

        else:

            self.fusion_module = None

        # ---------------------------------------------------------------
        # Output projection
        # ---------------------------------------------------------------

        if fusion_type == "concat":

            fusion_input_dim = (
                fusion_dim * len(self.modalities)
            )

        else:

            fusion_input_dim = fusion_dim

        self.output_projection = nn.Sequential(
            nn.LayerNorm(fusion_input_dim),
            nn.Linear(
                fusion_input_dim,
                hidden_dim,
            ),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(
                hidden_dim,
                output_dim,
            ),
        )

    # -------------------------------------------------------------------
    # Modality dropout
    # -------------------------------------------------------------------

    def _apply_modality_dropout(
        self,
        mask: torch.Tensor,
    ) -> torch.Tensor:
        """
        Randomly remove modalities during training.

        At least one modality remains available per sample whenever
        possible.
        """

        if (
            not self.training
            or self.modality_dropout <= 0.0
        ):
            return mask

        random_values = torch.rand_like(
            mask.float()
        )

        drop = (
            random_values
            < self.modality_dropout
        )

        new_mask = mask & ~drop

        # Ensure at least one modality remains.
        for i in range(new_mask.shape[0]):

            if not new_mask[i].any():

                available = torch.where(
                    mask[i]
                )[0]

                if len(available) > 0:

                    selected = available[
                        torch.randint(
                            len(available),
                            (1,),
                            device=available.device,
                        )
                    ]

                    new_mask[
                        i,
                        selected,
                    ] = True

        return new_mask

    # -------------------------------------------------------------------
    # Input preparation
    # -------------------------------------------------------------------

    def _prepare_inputs(
        self,
        inputs: Mapping[str, Optional[torch.Tensor]],
    ) -> Tuple[
        torch.Tensor,
        torch.Tensor,
    ]:
        """
        Convert dictionary of modality embeddings into a tensor.

        Returns
        -------
        x:
            [batch, modalities, fusion_dim]

        mask:
            [batch, modalities]
        """

        if not inputs:
            raise ValueError(
                "inputs cannot be empty"
            )

        # ---------------------------------------------------------------
        # Determine batch size.
        # ---------------------------------------------------------------

        batch_size = None

        for modality in self.modalities:

            value = inputs.get(modality)

            if value is None:
                continue

            value = _ensure_2d(
                value,
                expected_dim=self.modality_dims[modality],
                name=modality,
            )

            if batch_size is None:

                batch_size = value.shape[0]

            elif value.shape[0] != batch_size:

                raise ValueError(
                    f"Batch size mismatch for modality '{modality}'. "
                    f"Expected {batch_size}, got {value.shape[0]}"
                )

        if batch_size is None:

            raise ValueError(
                "At least one modality must be provided."
            )

        # ---------------------------------------------------------------
        # Determine device.
        # ---------------------------------------------------------------

        device = None

        for value in inputs.values():

            if value is not None:

                device = value.device
                break

        if device is None:

            device = next(
                self.parameters()
            ).device

        # ---------------------------------------------------------------
        # Build modality tensors.
        # ---------------------------------------------------------------

        projected = []

        availability = []

        for modality in self.modalities:

            value = inputs.get(modality)

            if value is None:

                projected.append(
                    torch.zeros(
                        batch_size,
                        self.fusion_dim,
                        device=device,
                    )
                )

                availability.append(
                    torch.zeros(
                        batch_size,
                        dtype=torch.bool,
                        device=device,
                    )
                )

                continue

            value = _ensure_2d(
                value,
                expected_dim=self.modality_dims[modality],
                name=modality,
            )

            projected_value = self.projectors[
                modality
            ](value)

            projected.append(
                projected_value
            )

            availability.append(
                torch.ones(
                    batch_size,
                    dtype=torch.bool,
                    device=value.device,
                )
            )

        x = torch.stack(
            projected,
            dim=1,
        )

        mask = torch.stack(
            availability,
            dim=1,
        )

        # ---------------------------------------------------------------
        # Add modality identity embeddings.
        # ---------------------------------------------------------------

        if self.use_modality_embeddings:

            modality_embedding = (
                self.modality_embeddings
                .unsqueeze(0)
                .expand(
                    batch_size,
                    -1,
                    -1,
                )
            )

            x = x + modality_embedding

        return x, mask

    # -------------------------------------------------------------------
    # Forward
    # -------------------------------------------------------------------

    def forward(
        self,
        inputs: Mapping[str, Optional[torch.Tensor]],
        return_modality_embeddings: bool = False,
    ) -> Dict[str, torch.Tensor]:
        """
        Perform multimodal fusion.

        Parameters
        ----------
        inputs:
            Dictionary mapping modality name to embedding.

            Example:

                {
                    "image": image_embedding,
                    "rna": rna_embedding,
                    "hand": hand_embedding,
                }

            Missing modalities may be None or omitted.

        return_modality_embeddings:
            If True, return projected modality embeddings.

        Returns
        -------
        Dictionary containing:

            fused_embedding
            modality_mask
            modality_weights

        Optionally:

            modality_embeddings
        """

        x, modality_mask = self._prepare_inputs(
            inputs
        )

        # ---------------------------------------------------------------
        # Modality dropout.
        # ---------------------------------------------------------------

        modality_mask = (
            self._apply_modality_dropout(
                modality_mask
            )
        )

        # Zero out unavailable modalities.
        x = x * modality_mask.unsqueeze(-1).float()

        # ---------------------------------------------------------------
        # Fusion.
        # ---------------------------------------------------------------

        modality_weights = None

        if self.fusion_type == "concat":

            fused = x.reshape(
                x.shape[0],
                -1,
            )

        elif self.fusion_type == "mean":

            fused = masked_mean(
                x,
                modality_mask.unsqueeze(-1),
                dim=1,
            )

        elif self.fusion_type == "sum":

            fused = (
                x
                * modality_mask.unsqueeze(-1).float()
            ).sum(dim=1)

        elif self.fusion_type == "attention":

            fused, modality_weights = (
                self.fusion_module(
                    x,
                    modality_mask=modality_mask,
                )
            )

        elif self.fusion_type == "gated":

            fused, modality_weights = (
                self.fusion_module(
                    x,
                    modality_mask=modality_mask,
                )
            )

        else:

            raise RuntimeError(
                f"Unsupported fusion type: "
                f"{self.fusion_type}"
            )

        # ---------------------------------------------------------------
        # Final projection.
        # ---------------------------------------------------------------

        fused = self.output_projection(
            fused
        )

        if self.normalize:

            fused = F.normalize(
                fused,
                p=2,
                dim=-1,
            )

        output = {
            "fused_embedding": fused,
            "modality_mask": modality_mask,
        }

        if modality_weights is not None:

            output[
                "modality_weights"
            ] = modality_weights

        if return_modality_embeddings:

            output[
                "modality_embeddings"
            ] = x

        return output

    # -------------------------------------------------------------------
    # Convenience methods
    # -------------------------------------------------------------------

    def available_modalities(
        self,
        inputs: Mapping[str, Optional[torch.Tensor]],
    ) -> List[str]:
        """
        Return modalities present in the input dictionary.
        """

        return [
            modality
            for modality in self.modalities
            if inputs.get(modality) is not None
        ]

    def modality_mask_from_inputs(
        self,
        inputs: Mapping[str, Optional[torch.Tensor]],
    ) -> torch.Tensor:
        """
        Return the availability mask without running fusion.
        """

        _, mask = self._prepare_inputs(
            inputs
        )

        return mask


# ---------------------------------------------------------------------------
# Simple concatenation fusion
# ---------------------------------------------------------------------------


class ConcatenationFusion(nn.Module):
    """
    Simple baseline fusion.

    Useful as a reference model before using attention or gated fusion.
    """

    def __init__(
        self,
        modality_dims: Mapping[str, int],
        output_dim: int = 512,
        hidden_dim: int = 512,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()

        self.modalities = list(
            modality_dims.keys()
        )

        input_dim = sum(
            modality_dims.values()
        )

        self.network = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(
                input_dim,
                hidden_dim,
            ),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(
                hidden_dim,
                output_dim,
            ),
        )

        self.modality_dims = dict(
            modality_dims
        )

    def forward(
        self,
        inputs: Mapping[str, torch.Tensor],
    ) -> torch.Tensor:
        """
        Concatenate modality embeddings.

        All modalities must be provided.
        """

        tensors = []

        for modality in self.modalities:

            if modality not in inputs:

                raise ValueError(
                    f"Missing required modality: "
                    f"{modality}"
                )

            x = _ensure_2d(
                inputs[modality],
                expected_dim=self.modality_dims[
                    modality
                ],
                name=modality,
            )

            tensors.append(x)

        concatenated = torch.cat(
            tensors,
            dim=-1,
        )

        return self.network(
            concatenated
        )


# ---------------------------------------------------------------------------
# Weighted fusion
# ---------------------------------------------------------------------------


class WeightedFusion(nn.Module):
    """
    Learnable global modality weights.

    Unlike attention fusion, these weights are not sample-dependent.

    This is useful as a lightweight baseline.
    """

    def __init__(
        self,
        modality_dims: Mapping[str, int],
        fusion_dim: int = 512,
        output_dim: int = 512,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()

        self.modalities = list(
            modality_dims.keys()
        )

        self.projectors = nn.ModuleDict()

        for modality, dim in modality_dims.items():

            self.projectors[modality] = (
                ModalityProjector(
                    input_dim=dim,
                    output_dim=fusion_dim,
                    dropout=dropout,
                )
            )

        self.modality_weights = nn.Parameter(
            torch.zeros(
                len(self.modalities)
            )
        )

        self.output = nn.Sequential(
            nn.LayerNorm(fusion_dim),
            nn.Linear(
                fusion_dim,
                output_dim,
            ),
        )

    def forward(
        self,
        inputs: Mapping[str, Optional[torch.Tensor]],
    ) -> Dict[str, torch.Tensor]:

        projected = []

        available = []

        reference = None

        for modality in self.modalities:

            value = inputs.get(modality)

            if value is not None:

                value = _ensure_2d(
                    value,
                    expected_dim=self.projectors[
                        modality
                    ].input_dim,
                    name=modality,
                )

                if reference is None:

                    reference = value

                projected.append(
                    self.projectors[
                        modality
                    ](value)
                )

                available.append(
                    modality
                )

        if not projected:

            raise ValueError(
                "No modality was provided."
            )

        x = torch.stack(
            projected,
            dim=1,
        )

        # Find corresponding modality weights.
        indices = [
            self.modalities.index(
                modality
            )
            for modality in available
        ]

        weights = self.modality_weights[
            indices
        ]

        weights = torch.softmax(
            weights,
            dim=0,
        )

        fused = torch.sum(
            x * weights.view(
                1,
                -1,
                1,
            ),
            dim=1,
        )

        fused = self.output(
            fused
        )

        fused = F.normalize(
            fused,
            p=2,
            dim=-1,
        )

        return {
            "fused_embedding": fused,
            "modality_weights": weights,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_fusion_model(
    modality_dims: Mapping[str, int],
    config: Optional[FusionConfig] = None,
) -> MultimodalFusionModel:
    """
    Factory function for the main fusion model.

    Example:

        config = FusionConfig(
            fusion_dim=512,
            output_dim=512,
            fusion_type="attention",
        )

        model = build_fusion_model(
            modality_dims={
                "image": 768,
                "cell": 256,
                "rna": 256,
                "hand": 128,
            },
            config=config,
        )
    """

    if config is None:

        config = FusionConfig()

    return MultimodalFusionModel(
        modality_dims=modality_dims,
        fusion_dim=config.fusion_dim,
        hidden_dim=config.hidden_dim,
        output_dim=config.output_dim,
        fusion_type=config.fusion_type,
        dropout=config.dropout,
        modality_dropout=config.modality_dropout,
        normalize=config.normalize,
        use_modality_embeddings=(
            config.use_modality_embeddings
        ),
    )


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


def _smoke_test() -> None:
    """
    Basic internal test.

    Run:

        python models/fusion_model.py
    """

    print("=" * 70)
    print("fusion_model.py smoke test")
    print("=" * 70)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    modality_dims = {
        "image": 768,
        "cell": 256,
        "wsi": 512,
        "rna": 256,
        "hand": 128,
    }

    model = MultimodalFusionModel(
        modality_dims=modality_dims,
        fusion_dim=512,
        hidden_dim=512,
        output_dim=512,
        fusion_type="attention",
        modality_dropout=0.1,
    ).to(device)

    model.train()

    batch_size = 4

    inputs = {
        "image": torch.randn(
            batch_size,
            768,
            device=device,
        ),
        "cell": torch.randn(
            batch_size,
            256,
            device=device,
        ),
        "wsi": torch.randn(
            batch_size,
            512,
            device=device,
        ),
        "rna": torch.randn(
            batch_size,
            256,
            device=device,
        ),
        "hand": torch.randn(
            batch_size,
            128,
            device=device,
        ),
    }

    output = model(
        inputs,
        return_modality_embeddings=True,
    )

    print(
        "Input modalities:",
        list(inputs.keys()),
    )

    print(
        "Fused embedding shape:",
        tuple(
            output[
                "fused_embedding"
            ].shape
        ),
    )

    print(
        "Modality mask:",
        output[
            "modality_mask"
        ],
    )

    if "modality_weights" in output:

        print(
            "Modality weights:",
            output[
                "modality_weights"
            ],
        )

    print(
        "Projected modality shape:",
        tuple(
            output[
                "modality_embeddings"
            ].shape
        ),
    )

    # Test missing modality.
    print("\nTesting missing modality...")

    incomplete_inputs = {
        "image": inputs["image"],
        "rna": inputs["rna"],
        "hand": inputs["hand"],
    }

    incomplete_output = model(
        incomplete_inputs
    )

    print(
        "Incomplete fusion shape:",
        tuple(
            incomplete_output[
                "fused_embedding"
            ].shape
        ),
    )

    print(
        "Incomplete modality mask:",
        incomplete_output[
            "modality_mask"
        ],
    )

    # Test backward pass.
    print("\nTesting backward pass...")

    loss = (
        output[
            "fused_embedding"
        ]
        .pow(2)
        .mean()
    )

    loss.backward()

    print(
        "Backward pass: OK"
    )

    print("=" * 70)
    print("Smoke test completed.")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    _smoke_test()