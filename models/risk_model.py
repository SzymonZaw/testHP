# models/risk_model.py

"""
Risk Model
==========

Moduł odpowiedzialny za estymację wielowymiarowego ryzyka na podstawie
cech pochodzących z różnych modalności:

- obrazów skóry,
- analizy komórkowej,
- RNA / transcriptomics,
- patologii,
- biologicznego wieku,
- anomalii,
- danych dłoni / morfologii,
- innych modeli multimodalnych.

Architektura została zaprojektowana tak, aby:
1. działała od razu z przykładowymi tensorami,
2. mogła zostać później zastąpiona modelem wytrenowanym,
3. obsługiwała brakujące modalności,
4. zwracała zarówno risk score, jak i confidence,
5. nie wykonywała decyzji klinicznych.

UWAGA:
Ten moduł jest warstwą modelową. Reguły decyzyjne i interpretacja
wyniku powinny znajdować się w:
    decision/
        decision_engine.py
        intervention_rules.py
        safety_rules.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class RiskModelConfig:
    """
    Configuration for RiskModel.

    Attributes
    ----------
    image_dim:
        Dimension of image embedding.

    cell_dim:
        Dimension of cellular embedding.

    rna_dim:
        Dimension of RNA embedding.

    pathology_dim:
        Dimension of pathology embedding.

    aging_dim:
        Dimension of biological-aging features.

    abnormality_dim:
        Dimension of abnormality features.

    hand_dim:
        Dimension of hand/morphology features.

    hidden_dim:
        Hidden dimension of the fusion network.

    num_risk_factors:
        Number of independent risk factors predicted by the model.

    dropout:
        Dropout probability.

    use_modality_gating:
        Whether to learn modality weights.

    risk_factors:
        Names of predicted risk factors.
    """

    image_dim: int = 768
    cell_dim: int = 256
    rna_dim: int = 512
    pathology_dim: int = 256
    aging_dim: int = 128
    abnormality_dim: int = 128
    hand_dim: int = 128

    hidden_dim: int = 256

    num_risk_factors: int = 5

    dropout: float = 0.2

    use_modality_gating: bool = True

    risk_factors: Tuple[str, ...] = (
        "skin_abnormality",
        "pathology",
        "biological_aging",
        "progression",
        "overall",
    )


# ============================================================================
# Utility modules
# ============================================================================


class MLPBlock(nn.Module):
    """
    Basic MLP block.

    Linear -> LayerNorm -> GELU -> Dropout
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.block = nn.Sequential(
            nn.Linear(input_dim, output_dim),
            nn.LayerNorm(output_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class ModalityEncoder(nn.Module):
    """
    Encodes one modality into a common latent representation.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


# ============================================================================
# Risk Model
# ============================================================================


class RiskModel(nn.Module):
    """
    Multimodal risk estimation model.

    The model receives embeddings from different components of the project
    and maps them into a shared latent space.

    Supported modalities
    --------------------
    image
    cell
    rna
    pathology
    aging
    abnormality
    hand

    Missing modalities are supported. If a modality is None, its contribution
    is ignored and the remaining modalities are renormalized.

    Output
    ------
    Dictionary containing:

        risk_scores
        overall_risk
        confidence
        modality_weights
        embeddings
    """

    def __init__(
        self,
        config: Optional[RiskModelConfig] = None,
    ) -> None:
        super().__init__()

        self.config = config or RiskModelConfig()

        # ------------------------------------------------------------
        # Individual modality encoders
        # ------------------------------------------------------------

        self.image_encoder = ModalityEncoder(
            self.config.image_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.cell_encoder = ModalityEncoder(
            self.config.cell_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.rna_encoder = ModalityEncoder(
            self.config.rna_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.pathology_encoder = ModalityEncoder(
            self.config.pathology_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.aging_encoder = ModalityEncoder(
            self.config.aging_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.abnormality_encoder = ModalityEncoder(
            self.config.abnormality_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.hand_encoder = ModalityEncoder(
            self.config.hand_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        # ------------------------------------------------------------
        # Modality gating
        # ------------------------------------------------------------

        self.modality_names = (
            "image",
            "cell",
            "rna",
            "pathology",
            "aging",
            "abnormality",
            "hand",
        )

        if self.config.use_modality_gating:

            self.modality_gate = nn.Sequential(
                nn.Linear(
                    self.config.hidden_dim,
                    self.config.hidden_dim // 2,
                ),
                nn.GELU(),
                nn.Linear(
                    self.config.hidden_dim // 2,
                    1,
                ),
            )

        else:
            self.modality_gate = None

        # ------------------------------------------------------------
        # Fusion
        # ------------------------------------------------------------

        self.fusion = nn.Sequential(
            nn.Linear(
                self.config.hidden_dim,
                self.config.hidden_dim,
            ),
            nn.LayerNorm(self.config.hidden_dim),
            nn.GELU(),
            nn.Dropout(self.config.dropout),

            nn.Linear(
                self.config.hidden_dim,
                self.config.hidden_dim,
            ),
            nn.LayerNorm(self.config.hidden_dim),
            nn.GELU(),
        )

        # ------------------------------------------------------------
        # Risk heads
        # ------------------------------------------------------------

        self.risk_head = nn.Sequential(
            nn.Linear(
                self.config.hidden_dim,
                self.config.hidden_dim // 2,
            ),
            nn.GELU(),
            nn.Dropout(self.config.dropout),

            nn.Linear(
                self.config.hidden_dim // 2,
                self.config.num_risk_factors,
            ),
        )

        # ------------------------------------------------------------
        # Confidence head
        # ------------------------------------------------------------

        self.confidence_head = nn.Sequential(
            nn.Linear(
                self.config.hidden_dim,
                self.config.hidden_dim // 2,
            ),
            nn.GELU(),

            nn.Linear(
                self.config.hidden_dim // 2,
                1,
            ),
        )

    # ========================================================================
    # Encoding
    # ========================================================================

    def encode_modalities(
        self,
        image: Optional[torch.Tensor] = None,
        cell: Optional[torch.Tensor] = None,
        rna: Optional[torch.Tensor] = None,
        pathology: Optional[torch.Tensor] = None,
        aging: Optional[torch.Tensor] = None,
        abnormality: Optional[torch.Tensor] = None,
        hand: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Encode all available modalities.

        Returns
        -------
        dict
            Dictionary containing encoded modality representations.
        """

        encoded: Dict[str, torch.Tensor] = {}

        if image is not None:
            encoded["image"] = self.image_encoder(image)

        if cell is not None:
            encoded["cell"] = self.cell_encoder(cell)

        if rna is not None:
            encoded["rna"] = self.rna_encoder(rna)

        if pathology is not None:
            encoded["pathology"] = self.pathology_encoder(pathology)

        if aging is not None:
            encoded["aging"] = self.aging_encoder(aging)

        if abnormality is not None:
            encoded["abnormality"] = self.abnormality_encoder(
                abnormality
            )

        if hand is not None:
            encoded["hand"] = self.hand_encoder(hand)

        return encoded

    # ========================================================================
    # Fusion
    # ========================================================================

    def fuse_modalities(
        self,
        encoded: Mapping[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Fuse available modality embeddings.

        Parameters
        ----------
        encoded:
            Dictionary of encoded modalities.

        Returns
        -------
        fused:
            Fused representation.

        weights:
            Learned modality weights.
        """

        if not encoded:
            raise ValueError(
                "At least one modality must be provided."
            )

        tensors = list(encoded.values())
        names = list(encoded.keys())

        stacked = torch.stack(tensors, dim=1)

        # ------------------------------------------------------------
        # Gated fusion
        # ------------------------------------------------------------

        if self.modality_gate is not None:

            gate_logits = self.modality_gate(
                stacked
            ).squeeze(-1)

            weights = torch.softmax(
                gate_logits,
                dim=1,
            )

        else:

            batch_size = stacked.shape[0]
            num_modalities = stacked.shape[1]

            weights = torch.ones(
                batch_size,
                num_modalities,
                device=stacked.device,
            )

            weights = weights / num_modalities

        fused = torch.sum(
            stacked * weights.unsqueeze(-1),
            dim=1,
        )

        fused = self.fusion(fused)

        modality_weights = {
            name: weights[:, index]
            for index, name in enumerate(names)
        }

        return fused, modality_weights

    # ========================================================================
    # Forward
    # ========================================================================

    def forward(
        self,
        image: Optional[torch.Tensor] = None,
        cell: Optional[torch.Tensor] = None,
        rna: Optional[torch.Tensor] = None,
        pathology: Optional[torch.Tensor] = None,
        aging: Optional[torch.Tensor] = None,
        abnormality: Optional[torch.Tensor] = None,
        hand: Optional[torch.Tensor] = None,
    ) -> Dict[str, object]:
        """
        Estimate multimodal risk.

        All tensors should have shape:

            [batch_size, feature_dimension]

        Example
        -------
        >>> output = model(
        ...     image=image_embedding,
        ...     rna=rna_embedding,
        ...     pathology=pathology_embedding,
        ... )
        """

        encoded = self.encode_modalities(
            image=image,
            cell=cell,
            rna=rna,
            pathology=pathology,
            aging=aging,
            abnormality=abnormality,
            hand=hand,
        )

        fused, modality_weights = self.fuse_modalities(
            encoded
        )

        # ------------------------------------------------------------
        # Risk prediction
        # ------------------------------------------------------------

        risk_logits = self.risk_head(
            fused
        )

        risk_scores = torch.sigmoid(
            risk_logits
        )

        # ------------------------------------------------------------
        # Confidence
        # ------------------------------------------------------------

        confidence_logits = self.confidence_head(
            fused
        )

        confidence = torch.sigmoid(
            confidence_logits
        )

        # ------------------------------------------------------------
        # Overall risk
        #
        # The final risk factor is explicitly treated as the overall
        # risk when configured accordingly.
        # ------------------------------------------------------------

        if "overall" in self.config.risk_factors:

            overall_index = self.config.risk_factors.index(
                "overall"
            )

            overall_risk = risk_scores[
                :,
                overall_index,
            ]

        else:

            overall_risk = risk_scores.mean(
                dim=-1
            )

        return {
            "risk_scores": risk_scores,
            "overall_risk": overall_risk,
            "confidence": confidence,
            "modality_weights": modality_weights,
            "embeddings": encoded,
            "fused_embedding": fused,
        }

    # ========================================================================
    # Convenience API
    # ========================================================================

    @torch.no_grad()
    def predict(
        self,
        **kwargs: torch.Tensor,
    ) -> Dict[str, object]:
        """
        Inference wrapper.

        Automatically switches the model to evaluation mode.
        """

        was_training = self.training

        self.eval()

        output = self.forward(**kwargs)

        if was_training:
            self.train()

        return output

    # ========================================================================
    # Risk interpretation
    # ========================================================================

    def interpret_risk(
        self,
        risk_scores: torch.Tensor,
    ) -> List[Dict[str, float]]:
        """
        Convert raw risk tensor into a Python-friendly structure.

        Parameters
        ----------
        risk_scores:
            Tensor of shape [batch_size, num_risk_factors].

        Returns
        -------
        list of dictionaries
        """

        if risk_scores.ndim != 2:
            raise ValueError(
                "risk_scores must have shape "
                "[batch_size, num_risk_factors]."
            )

        results: List[Dict[str, float]] = []

        for row in risk_scores:

            sample = {}

            for index, factor in enumerate(
                self.config.risk_factors
            ):
                sample[factor] = float(
                    row[index].detach().cpu()
                )

            results.append(sample)

        return results

    # ========================================================================
    # Modality availability
    # ========================================================================

    @staticmethod
    def calculate_modality_coverage(
        available_modalities: Iterable[str],
        all_modalities: Optional[Sequence[str]] = None,
    ) -> float:
        """
        Calculate fraction of available modalities.

        Example
        -------
        3 available modalities out of 7 -> 0.4286
        """

        if all_modalities is None:

            all_modalities = (
                "image",
                "cell",
                "rna",
                "pathology",
                "aging",
                "abnormality",
                "hand",
            )

        available = set(available_modalities)

        valid = available.intersection(
            all_modalities
        )

        return len(valid) / len(all_modalities)

    # ========================================================================
    # Parameter utilities
    # ========================================================================

    def freeze_encoders(self) -> None:
        """
        Freeze modality encoders.

        Useful when pretrained embeddings are treated as fixed features.
        """

        encoders = (
            self.image_encoder,
            self.cell_encoder,
            self.rna_encoder,
            self.pathology_encoder,
            self.aging_encoder,
            self.abnormality_encoder,
            self.hand_encoder,
        )

        for encoder in encoders:

            for parameter in encoder.parameters():
                parameter.requires_grad = False

    def unfreeze_encoders(self) -> None:
        """
        Unfreeze modality encoders.
        """

        encoders = (
            self.image_encoder,
            self.cell_encoder,
            self.rna_encoder,
            self.pathology_encoder,
            self.aging_encoder,
            self.abnormality_encoder,
            self.hand_encoder,
        )

        for encoder in encoders:

            for parameter in encoder.parameters():
                parameter.requires_grad = True


# ============================================================================
# Loss
# ============================================================================


class RiskLoss(nn.Module):
    """
    Loss function for multi-factor risk prediction.

    Uses BCEWithLogitsLoss.

    Expected target:

        [batch_size, num_risk_factors]

    Values should normally be in [0, 1].
    """

    def __init__(
        self,
        pos_weight: Optional[torch.Tensor] = None,
    ) -> None:
        super().__init__()

        self.loss = nn.BCEWithLogitsLoss(
            pos_weight=pos_weight
        )

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:

        if logits.shape != targets.shape:
            raise ValueError(
                "Logits and targets must have identical shapes."
            )

        return self.loss(
            logits,
            targets,
        )


# ============================================================================
# Helper functions
# ============================================================================


def create_risk_model(
    config: Optional[RiskModelConfig] = None,
    checkpoint: Optional[str] = None,
    device: Optional[str] = None,
) -> RiskModel:
    """
    Create and optionally load a RiskModel.

    Parameters
    ----------
    config:
        RiskModelConfig.

    checkpoint:
        Optional path to checkpoint.

    device:
        "cuda", "cpu", "mps", etc.

    Returns
    -------
    RiskModel
    """

    model = RiskModel(
        config=config
    )

    if checkpoint is not None:

        state = torch.load(
            checkpoint,
            map_location="cpu",
        )

        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]

        model.load_state_dict(
            state,
            strict=False,
        )

    if device is not None:

        model = model.to(device)

    return model


def risk_level(
    score: float,
) -> str:
    """
    Convert continuous score into a coarse risk category.

    IMPORTANT:
    These thresholds are placeholders for development only.
    They should NOT be treated as clinical thresholds.
    """

    if not 0.0 <= score <= 1.0:
        raise ValueError(
            "Risk score must be between 0 and 1."
        )

    if score < 0.33:
        return "low"

    if score < 0.66:
        return "moderate"

    return "high"


# ============================================================================
# Example
# ============================================================================


if __name__ == "__main__":

    # ------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------

    config = RiskModelConfig(
        image_dim=768,
        cell_dim=256,
        rna_dim=512,
        pathology_dim=256,
        aging_dim=128,
        abnormality_dim=128,
        hand_dim=128,
        hidden_dim=256,
    )

    # ------------------------------------------------------------
    # Model
    # ------------------------------------------------------------

    model = RiskModel(config)

    # ------------------------------------------------------------
    # Example embeddings
    # ------------------------------------------------------------

    batch_size = 4

    image_embedding = torch.randn(
        batch_size,
        config.image_dim,
    )

    rna_embedding = torch.randn(
        batch_size,
        config.rna_dim,
    )

    pathology_embedding = torch.randn(
        batch_size,
        config.pathology_dim,
    )

    aging_embedding = torch.randn(
        batch_size,
        config.aging_dim,
    )

    # ------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------

    output = model.predict(
        image=image_embedding,
        rna=rna_embedding,
        pathology=pathology_embedding,
        aging=aging_embedding,
    )

    # ------------------------------------------------------------
    # Display
    # ------------------------------------------------------------

    print(
        "Risk scores:",
        output["risk_scores"].shape,
    )

    print(
        "Overall risk:",
        output["overall_risk"].shape,
    )

    print(
        "Confidence:",
        output["confidence"].shape,
    )

    print(
        "\nRisk interpretation:"
    )

    interpretations = model.interpret_risk(
        output["risk_scores"]
    )

    for index, sample in enumerate(
        interpretations
    ):

        print(
            f"Sample {index}:"
        )

        for factor, score in sample.items():

            print(
                f"  {factor}: "
                f"{score:.3f} "
                f"({risk_level(score)})"
            )

    # ------------------------------------------------------------
    # Modality weights
    # ------------------------------------------------------------

    print(
        "\nModality weights:"
    )

    for modality, weight in output[
        "modality_weights"
    ].items():

        print(
            f"  {modality}: "
            f"{weight.mean().item():.3f}"
        )