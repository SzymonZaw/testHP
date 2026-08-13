# models/intervention_model.py

"""
Intervention Model
==================

Model odpowiedzialny za generowanie i ranking potencjalnych interwencji
na podstawie stanu biologicznego oraz wyników innych modeli.

Główne wejścia:
    - risk_model
    - aging_model
    - abnormality_model
    - pathology_model
    - multimodal/fusion model
    - longitudinal model (opcjonalnie)

Główne wyjścia:
    - score każdej potencjalnej interwencji,
    - ranking interwencji,
    - confidence,
    - uzasadnienie oparte na cechach wejściowych.

WAŻNE:
--------
Ten moduł NIE podejmuje samodzielnie decyzji klinicznych.

Ostateczna logika:
    intervention_model.py
            |
            v
    decision/decision_engine.py
            |
            +--> safety_rules.py
            +--> intervention_rules.py
            +--> monitoring_rules.py
            +--> confidence.py

Model może sugerować/rankować interwencje, ale ich zastosowanie
powinno być filtrowane przez warstwę decision/.
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
class InterventionModelConfig:
    """
    Configuration of InterventionModel.

    Parameters
    ----------
    risk_dim:
        Dimension of risk-model embedding.

    aging_dim:
        Dimension of biological-aging embedding.

    abnormality_dim:
        Dimension of abnormality embedding.

    pathology_dim:
        Dimension of pathology embedding.

    longitudinal_dim:
        Dimension of longitudinal-state embedding.

    fusion_dim:
        Dimension of multimodal/fusion embedding.

    hidden_dim:
        Hidden dimension used by the intervention network.

    num_interventions:
        Number of intervention classes.

    dropout:
        Dropout probability.

    interventions:
        Names of available intervention classes.
    """

    risk_dim: int = 128
    aging_dim: int = 128
    abnormality_dim: int = 128
    pathology_dim: int = 256
    longitudinal_dim: int = 128
    fusion_dim: int = 256

    hidden_dim: int = 256

    num_interventions: int = 8

    dropout: float = 0.2

    interventions: Tuple[str, ...] = (
        "monitoring",
        "preventive_care",
        "dermatological_assessment",
        "diagnostic_followup",
        "specialist_consultation",
        "additional_imaging",
        "additional_laboratory_testing",
        "no_immediate_action",
    )


# ============================================================================
# Utility modules
# ============================================================================


class FeatureEncoder(nn.Module):
    """
    Encodes an input feature vector into the common latent space.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(
                input_dim,
                hidden_dim,
            ),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),

            nn.Linear(
                hidden_dim,
                hidden_dim,
            ),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:

        return self.network(x)


# ============================================================================
# Intervention Model
# ============================================================================


class InterventionModel(nn.Module):
    """
    Multimodal intervention-ranking model.

    The model accepts optional embeddings from:

        risk
        aging
        abnormality
        pathology
        longitudinal
        fusion

    Missing modalities are supported.

    The model produces:

        intervention_scores
        intervention_probabilities
        confidence
        modality_weights
        fused_embedding
    """

    def __init__(
        self,
        config: Optional[InterventionModelConfig] = None,
    ) -> None:
        super().__init__()

        self.config = (
            config
            if config is not None
            else InterventionModelConfig()
        )

        # ------------------------------------------------------------------
        # Encoders
        # ------------------------------------------------------------------

        self.risk_encoder = FeatureEncoder(
            self.config.risk_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.aging_encoder = FeatureEncoder(
            self.config.aging_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.abnormality_encoder = FeatureEncoder(
            self.config.abnormality_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.pathology_encoder = FeatureEncoder(
            self.config.pathology_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.longitudinal_encoder = FeatureEncoder(
            self.config.longitudinal_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        self.fusion_encoder = FeatureEncoder(
            self.config.fusion_dim,
            self.config.hidden_dim,
            self.config.dropout,
        )

        # ------------------------------------------------------------------
        # Modality gating
        # ------------------------------------------------------------------

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

        # ------------------------------------------------------------------
        # Main fusion network
        # ------------------------------------------------------------------

        self.fusion = nn.Sequential(
            nn.Linear(
                self.config.hidden_dim,
                self.config.hidden_dim,
            ),
            nn.LayerNorm(
                self.config.hidden_dim
            ),
            nn.GELU(),
            nn.Dropout(
                self.config.dropout
            ),

            nn.Linear(
                self.config.hidden_dim,
                self.config.hidden_dim,
            ),
            nn.LayerNorm(
                self.config.hidden_dim
            ),
            nn.GELU(),
        )

        # ------------------------------------------------------------------
        # Intervention prediction head
        # ------------------------------------------------------------------

        self.intervention_head = nn.Sequential(
            nn.Linear(
                self.config.hidden_dim,
                self.config.hidden_dim // 2,
            ),
            nn.GELU(),
            nn.Dropout(
                self.config.dropout
            ),

            nn.Linear(
                self.config.hidden_dim // 2,
                self.config.num_interventions,
            ),
        )

        # ------------------------------------------------------------------
        # Confidence head
        # ------------------------------------------------------------------

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
        risk: Optional[torch.Tensor] = None,
        aging: Optional[torch.Tensor] = None,
        abnormality: Optional[torch.Tensor] = None,
        pathology: Optional[torch.Tensor] = None,
        longitudinal: Optional[torch.Tensor] = None,
        fusion: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Encode all available modalities.

        Returns
        -------
        dict
            Encoded feature representations.
        """

        encoded: Dict[str, torch.Tensor] = {}

        if risk is not None:
            encoded["risk"] = self.risk_encoder(
                risk
            )

        if aging is not None:
            encoded["aging"] = self.aging_encoder(
                aging
            )

        if abnormality is not None:
            encoded["abnormality"] = (
                self.abnormality_encoder(
                    abnormality
                )
            )

        if pathology is not None:
            encoded["pathology"] = (
                self.pathology_encoder(
                    pathology
                )
            )

        if longitudinal is not None:
            encoded["longitudinal"] = (
                self.longitudinal_encoder(
                    longitudinal
                )
            )

        if fusion is not None:
            encoded["fusion"] = (
                self.fusion_encoder(
                    fusion
                )
            )

        return encoded

    # ========================================================================
    # Fusion
    # ========================================================================

    def fuse_modalities(
        self,
        encoded: Mapping[str, torch.Tensor],
    ) -> Tuple[
        torch.Tensor,
        Dict[str, torch.Tensor],
    ]:
        """
        Fuse available modalities.

        Missing modalities are simply omitted.

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

        names = list(
            encoded.keys()
        )

        tensors = list(
            encoded.values()
        )

        stacked = torch.stack(
            tensors,
            dim=1,
        )

        # ------------------------------------------------------------
        # Gating
        # ------------------------------------------------------------

        gate_logits = self.modality_gate(
            stacked
        ).squeeze(-1)

        weights = torch.softmax(
            gate_logits,
            dim=1,
        )

        # ------------------------------------------------------------
        # Weighted fusion
        # ------------------------------------------------------------

        fused = torch.sum(
            stacked
            * weights.unsqueeze(-1),
            dim=1,
        )

        fused = self.fusion(
            fused
        )

        modality_weights = {
            name: weights[:, index]
            for index, name in enumerate(
                names
            )
        }

        return (
            fused,
            modality_weights,
        )

    # ========================================================================
    # Forward
    # ========================================================================

    def forward(
        self,
        risk: Optional[torch.Tensor] = None,
        aging: Optional[torch.Tensor] = None,
        abnormality: Optional[torch.Tensor] = None,
        pathology: Optional[torch.Tensor] = None,
        longitudinal: Optional[torch.Tensor] = None,
        fusion: Optional[torch.Tensor] = None,
    ) -> Dict[str, object]:
        """
        Predict intervention scores.

        Parameters
        ----------
        risk:
            Risk-model representation.

        aging:
            Biological-aging representation.

        abnormality:
            Abnormality representation.

        pathology:
            Pathology representation.

        longitudinal:
            Longitudinal representation.

        fusion:
            Multimodal fusion representation.

        Returns
        -------
        dict
            Intervention prediction output.
        """

        encoded = self.encode_modalities(
            risk=risk,
            aging=aging,
            abnormality=abnormality,
            pathology=pathology,
            longitudinal=longitudinal,
            fusion=fusion,
        )

        fused, modality_weights = (
            self.fuse_modalities(
                encoded
            )
        )

        # ------------------------------------------------------------
        # Intervention logits
        # ------------------------------------------------------------

        intervention_logits = (
            self.intervention_head(
                fused
            )
        )

        # Softmax because interventions are represented
        # as mutually ranked alternatives at this stage.
        intervention_probabilities = (
            torch.softmax(
                intervention_logits,
                dim=-1,
            )
        )

        # ------------------------------------------------------------
        # Confidence
        # ------------------------------------------------------------

        confidence_logits = (
            self.confidence_head(
                fused
            )
        )

        confidence = torch.sigmoid(
            confidence_logits
        )

        # ------------------------------------------------------------
        # Ranking
        # ------------------------------------------------------------

        ranking = torch.argsort(
            intervention_probabilities,
            dim=-1,
            descending=True,
        )

        return {
            "intervention_logits": (
                intervention_logits
            ),
            "intervention_probabilities": (
                intervention_probabilities
            ),
            "confidence": confidence,
            "modality_weights": modality_weights,
            "embeddings": encoded,
            "fused_embedding": fused,
            "ranking": ranking,
        }

    # ========================================================================
    # Prediction
    # ========================================================================

    @torch.no_grad()
    def predict(
        self,
        **kwargs: torch.Tensor,
    ) -> Dict[str, object]:
        """
        Inference wrapper.

        Automatically switches model to evaluation mode.
        """

        was_training = self.training

        self.eval()

        output = self.forward(
            **kwargs
        )

        if was_training:
            self.train()

        return output

    # ========================================================================
    # Ranking API
    # ========================================================================

    def rank_interventions(
        self,
        probabilities: torch.Tensor,
        top_k: Optional[int] = None,
    ) -> List[List[Dict[str, object]]]:
        """
        Convert intervention probabilities into a ranked list.

        Parameters
        ----------
        probabilities:
            Tensor of shape:

                [batch_size, num_interventions]

        top_k:
            Number of interventions to return.

        Returns
        -------
        list
            Ranked interventions for each sample.
        """

        if probabilities.ndim != 2:
            raise ValueError(
                "probabilities must have shape "
                "[batch_size, num_interventions]."
            )

        if probabilities.shape[-1] != (
            self.config.num_interventions
        ):
            raise ValueError(
                "Unexpected number of intervention classes."
            )

        if top_k is None:
            top_k = self.config.num_interventions

        top_k = min(
            top_k,
            self.config.num_interventions,
        )

        values, indices = torch.topk(
            probabilities,
            k=top_k,
            dim=-1,
        )

        results: List[
            List[Dict[str, object]]
        ] = []

        for batch_index in range(
            probabilities.shape[0]
        ):

            sample_results = []

            for rank in range(top_k):

                intervention_index = int(
                    indices[
                        batch_index,
                        rank
                    ].item()
                )

                score = float(
                    values[
                        batch_index,
                        rank
                    ].item()
                )

                intervention_name = (
                    self.config.interventions[
                        intervention_index
                    ]
                )

                sample_results.append(
                    {
                        "rank": rank + 1,
                        "intervention": (
                            intervention_name
                        ),
                        "score": score,
                    }
                )

            results.append(
                sample_results
            )

        return results

    # ========================================================================
    # Feature-based explanation
    # ========================================================================

    def explain_prediction(
        self,
        output: Mapping[str, object],
        sample_index: int = 0,
        top_k: int = 3,
    ) -> Dict[str, object]:
        """
        Provide a lightweight model-level explanation.

        This does NOT attempt to provide clinical causality.

        The explanation is based primarily on the learned modality weights.

        Returns
        -------
        dict
            Top interventions and influential modalities.
        """

        probabilities = output[
            "intervention_probabilities"
        ]

        modality_weights = output[
            "modality_weights"
        ]

        confidence = output[
            "confidence"
        ]

        if not isinstance(
            probabilities,
            torch.Tensor,
        ):
            raise TypeError(
                "Invalid intervention probabilities."
            )

        if not isinstance(
            confidence,
            torch.Tensor,
        ):
            raise TypeError(
                "Invalid confidence tensor."
            )

        ranking = self.rank_interventions(
            probabilities,
            top_k=top_k,
        )

        modality_importance = {}

        if isinstance(
            modality_weights,
            Mapping,
        ):

            for name, weight in (
                modality_weights.items()
            ):

                if not isinstance(
                    weight,
                    torch.Tensor,
                ):
                    continue

                modality_importance[name] = (
                    float(
                        weight[
                            sample_index
                        ].detach().cpu()
                    )
                )

        sorted_modalities = sorted(
            modality_importance.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return {
            "top_interventions": ranking[
                sample_index
            ],
            "confidence": float(
                confidence[
                    sample_index
                ].detach().cpu()
            ),
            "modality_importance": (
                sorted_modalities
            ),
        }

    # ========================================================================
    # Model utilities
    # ========================================================================

    def freeze_encoders(self) -> None:
        """
        Freeze all modality encoders.
        """

        encoders = (
            self.risk_encoder,
            self.aging_encoder,
            self.abnormality_encoder,
            self.pathology_encoder,
            self.longitudinal_encoder,
            self.fusion_encoder,
        )

        for encoder in encoders:

            for parameter in (
                encoder.parameters()
            ):
                parameter.requires_grad = False

    def unfreeze_encoders(self) -> None:
        """
        Unfreeze all modality encoders.
        """

        encoders = (
            self.risk_encoder,
            self.aging_encoder,
            self.abnormality_encoder,
            self.pathology_encoder,
            self.longitudinal_encoder,
            self.fusion_encoder,
        )

        for encoder in encoders:

            for parameter in (
                encoder.parameters()
            ):
                parameter.requires_grad = True


# ============================================================================
# Loss
# ============================================================================


class InterventionLoss(nn.Module):
    """
    Cross-entropy loss for intervention classification/ranking.

    Expected target:

        [batch_size]

    where each value is an integer representing the target intervention.

    Example:

        target = tensor([0, 3, 7])
    """

    def __init__(
        self,
        label_smoothing: float = 0.0,
    ) -> None:
        super().__init__()

        self.loss = nn.CrossEntropyLoss(
            label_smoothing=label_smoothing
        )

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:

        if logits.ndim != 2:
            raise ValueError(
                "logits must have shape "
                "[batch_size, num_interventions]."
            )

        if targets.ndim != 1:
            raise ValueError(
                "targets must have shape "
                "[batch_size]."
            )

        return self.loss(
            logits,
            targets,
        )


# ============================================================================
# Intervention utilities
# ============================================================================


def intervention_name(
    index: int,
    interventions: Sequence[str],
) -> str:
    """
    Return intervention name for an integer class index.
    """

    if index < 0 or index >= len(
        interventions
    ):
        raise IndexError(
            "Intervention index out of range."
        )

    return interventions[index]


def intervention_index(
    name: str,
    interventions: Sequence[str],
) -> int:
    """
    Return class index for intervention name.
    """

    try:
        return interventions.index(
            name
        )

    except ValueError as exc:

        raise ValueError(
            f"Unknown intervention: {name}"
        ) from exc


# ============================================================================
# Model factory
# ============================================================================


def create_intervention_model(
    config: Optional[
        InterventionModelConfig
    ] = None,
    checkpoint: Optional[str] = None,
    device: Optional[str] = None,
) -> InterventionModel:
    """
    Create InterventionModel and optionally load checkpoint.
    """

    model = InterventionModel(
        config=config
    )

    if checkpoint is not None:

        state = torch.load(
            checkpoint,
            map_location="cpu",
        )

        if (
            isinstance(state, dict)
            and "state_dict" in state
        ):
            state = state[
                "state_dict"
            ]

        model.load_state_dict(
            state,
            strict=False,
        )

    if device is not None:
        model = model.to(device)

    return model


# ============================================================================
# Example
# ============================================================================


if __name__ == "__main__":

    # ------------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------------

    config = (
        InterventionModelConfig(
            risk_dim=128,
            aging_dim=128,
            abnormality_dim=128,
            pathology_dim=256,
            longitudinal_dim=128,
            fusion_dim=256,
            hidden_dim=256,
        )
    )

    # ------------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------------

    model = InterventionModel(
        config
    )

    # ------------------------------------------------------------------------
    # Example embeddings
    # ------------------------------------------------------------------------

    batch_size = 4

    risk_embedding = torch.randn(
        batch_size,
        config.risk_dim,
    )

    aging_embedding = torch.randn(
        batch_size,
        config.aging_dim,
    )

    abnormality_embedding = (
        torch.randn(
            batch_size,
            config.abnormality_dim,
        )
    )

    pathology_embedding = (
        torch.randn(
            batch_size,
            config.pathology_dim,
        )
    )

    # ------------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------------

    output = model.predict(
        risk=risk_embedding,
        aging=aging_embedding,
        abnormality=abnormality_embedding,
        pathology=pathology_embedding,
    )

    # ------------------------------------------------------------------------
    # Shapes
    # ------------------------------------------------------------------------

    print(
        "Intervention probabilities:",
        output[
            "intervention_probabilities"
        ].shape,
    )

    print(
        "Confidence:",
        output[
            "confidence"
        ].shape,
    )

    # ------------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------------

    rankings = model.rank_interventions(
        output[
            "intervention_probabilities"
        ],
        top_k=5,
    )

    for index, sample in enumerate(
        rankings
    ):

        print(
            f"\nSample {index}:"
        )

        for item in sample:

            print(
                f"  {item['rank']}. "
                f"{item['intervention']} "
                f"({item['score']:.3f})"
            )

    # ------------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------------

    explanation = (
        model.explain_prediction(
            output,
            sample_index=0,
            top_k=3,
        )
    )

    print(
        "\nExplanation:"
    )

    print(
        "Confidence:",
        f"{explanation['confidence']:.3f}",
    )

    print(
        "Top interventions:"
    )

    for item in (
        explanation[
            "top_interventions"
        ]
    ):

        print(
            f"  {item['rank']}. "
            f"{item['intervention']} "
            f"({item['score']:.3f})"
        )

    print(
        "\nMost influential modalities:"
    )

    for name, weight in (
        explanation[
            "modality_importance"
        ]
    ):

        print(
            f"  {name}: "
            f"{weight:.3f}"
        )