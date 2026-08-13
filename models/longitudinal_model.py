# models/longitudinal_model.py

"""
Longitudinal Model
==================

Model odpowiedzialny za analizę zmian stanu biologicznego w czasie.

Obsługiwany schemat:

    T0 -> T1 -> T2 -> T3 -> ...

Każdy punkt czasowy może zawierać reprezentacje pochodzące z:

    - obrazów,
    - analizy komórkowej,
    - RNA,
    - patologii,
    - dłoni / cech fenotypowych,
    - fusion model,
    - risk model,
    - aging model.

Model realizuje trzy główne zadania:

    1. reprezentacja stanu w czasie,
    2. modelowanie dynamiki zmian,
    3. predykcja przyszłego stanu.

Architektura:

    temporal embeddings
            |
            v
       input projection
            |
            v
      Transformer Encoder
            |
            +--------> current state
            |
            +--------> temporal trend
            |
            +--------> future state
            |
            +--------> uncertainty

WAŻNE:
--------
Ten moduł nie podejmuje decyzji klinicznych.

Predykcja przyszłego stanu jest predykcją modelową.
Ostateczna interpretacja powinna przechodzić przez:

    analysis/
        |
        v
    decision/
        |
        +--> safety_rules.py
        +--> monitoring_rules.py
        +--> confidence.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class LongitudinalModelConfig:
    """
    Configuration of the longitudinal model.

    Parameters
    ----------
    input_dim:
        Dimension of the state embedding at each time point.

    hidden_dim:
        Internal temporal representation size.

    num_heads:
        Number of Transformer attention heads.

    num_layers:
        Number of Transformer encoder layers.

    feedforward_dim:
        Transformer feed-forward dimension.

    dropout:
        Dropout probability.

    max_timepoints:
        Maximum supported number of temporal observations.

    future_steps:
        Number of future states predicted by the model.

    output_dim:
        Dimension of predicted future-state embedding.
    """

    input_dim: int = 256

    hidden_dim: int = 256

    num_heads: int = 8

    num_layers: int = 4

    feedforward_dim: int = 1024

    dropout: float = 0.2

    max_timepoints: int = 16

    future_steps: int = 1

    output_dim: int = 256


# ============================================================================
# Positional Encoding
# ============================================================================


class TemporalPositionalEncoding(nn.Module):
    """
    Learnable temporal positional embeddings.

    Unlike conventional Transformer sinusoidal encoding, this module
    learns a separate embedding for each temporal position.

    Example:

        T0 -> position 0
        T1 -> position 1
        T2 -> position 2
        T3 -> position 3
    """

    def __init__(
        self,
        max_timepoints: int,
        hidden_dim: int,
    ) -> None:
        super().__init__()

        self.embedding = nn.Parameter(
            torch.zeros(
                1,
                max_timepoints,
                hidden_dim,
            )
        )

        nn.init.normal_(
            self.embedding,
            mean=0.0,
            std=0.02,
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        """
        Parameters
        ----------
        x:
            Tensor of shape:

                [batch, time, hidden_dim]

        Returns
        -------
        Tensor
            Position-enriched representation.
        """

        sequence_length = x.shape[1]

        if sequence_length > (
            self.embedding.shape[1]
        ):
            raise ValueError(
                "Sequence length exceeds "
                "max_timepoints."
            )

        return (
            x
            + self.embedding[
                :,
                :sequence_length,
                :,
            ]
        )


# ============================================================================
# Temporal Difference Encoder
# ============================================================================


class TemporalDifferenceEncoder(nn.Module):
    """
    Encodes temporal differences between consecutive states.

    Given:

        X0, X1, X2, X3

    calculates:

        X1 - X0
        X2 - X1
        X3 - X2

    These differences provide an explicit representation of biological
    change between visits.
    """

    def __init__(
        self,
        hidden_dim: int,
    ) -> None:
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(
                hidden_dim,
                hidden_dim,
            ),
            nn.LayerNorm(
                hidden_dim
            ),
            nn.GELU(),
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        """
        Parameters
        ----------
        x:
            [batch, time, hidden_dim]

        Returns
        -------
        Tensor
            [batch, time, hidden_dim]

        The first time point receives a zero difference.
        """

        if x.shape[1] == 1:

            differences = torch.zeros_like(
                x
            )

        else:

            delta = (
                x[:, 1:, :]
                - x[:, :-1, :]
            )

            first = torch.zeros_like(
                x[:, :1, :]
            )

            differences = torch.cat(
                [
                    first,
                    delta,
                ],
                dim=1,
            )

        return self.encoder(
            differences
        )


# ============================================================================
# Temporal Attention Pooling
# ============================================================================


class TemporalAttentionPooling(
    nn.Module
):
    """
    Learns which temporal observations are most informative.

    Produces:

        pooled representation
        temporal attention weights
    """

    def __init__(
        self,
        hidden_dim: int,
    ) -> None:
        super().__init__()

        self.score = nn.Sequential(
            nn.Linear(
                hidden_dim,
                hidden_dim // 2,
            ),
            nn.Tanh(),
            nn.Linear(
                hidden_dim // 2,
                1,
            ),
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[
        torch.Tensor,
        torch.Tensor,
    ]:
        """
        Parameters
        ----------
        x:
            [batch, time, hidden]

        mask:
            [batch, time]

            True = valid time point
            False = padding

        Returns
        -------
        pooled:
            [batch, hidden]

        weights:
            [batch, time]
        """

        scores = self.score(
            x
        ).squeeze(-1)

        if mask is not None:

            scores = scores.masked_fill(
                ~mask,
                -1e9,
            )

        weights = torch.softmax(
            scores,
            dim=1,
        )

        pooled = torch.sum(
            x
            * weights.unsqueeze(-1),
            dim=1,
        )

        return (
            pooled,
            weights,
        )


# ============================================================================
# Longitudinal Model
# ============================================================================


class LongitudinalModel(
    nn.Module
):
    """
    Transformer-based longitudinal model.

    Input:

        [batch, time, input_dim]

    Example:

        batch = 8
        time = 4
        input_dim = 256

        [8, 4, 256]

    where:

        time 0 = T0
        time 1 = T1
        time 2 = T2
        time 3 = T3

    Outputs:

        temporal_embeddings
        current_state
        temporal_trend
        future_state
        uncertainty
        temporal_attention
    """

    def __init__(
        self,
        config: Optional[
            LongitudinalModelConfig
        ] = None,
    ) -> None:
        super().__init__()

        self.config = (
            config
            if config is not None
            else LongitudinalModelConfig()
        )

        # ------------------------------------------------------------------
        # Input projection
        # ------------------------------------------------------------------

        self.input_projection = nn.Sequential(
            nn.Linear(
                self.config.input_dim,
                self.config.hidden_dim,
            ),
            nn.LayerNorm(
                self.config.hidden_dim
            ),
            nn.GELU(),
            nn.Dropout(
                self.config.dropout
            ),
        )

        # ------------------------------------------------------------------
        # Temporal position
        # ------------------------------------------------------------------

        self.temporal_position = (
            TemporalPositionalEncoding(
                self.config.max_timepoints,
                self.config.hidden_dim,
            )
        )

        # ------------------------------------------------------------------
        # Explicit temporal difference
        # ------------------------------------------------------------------

        self.difference_encoder = (
            TemporalDifferenceEncoder(
                self.config.hidden_dim
            )
        )

        # ------------------------------------------------------------------
        # Transformer
        # ------------------------------------------------------------------

        encoder_layer = (
            nn.TransformerEncoderLayer(
                d_model=self.config.hidden_dim,
                nhead=self.config.num_heads,
                dim_feedforward=(
                    self.config.feedforward_dim
                ),
                dropout=self.config.dropout,
                activation="gelu",
                batch_first=True,
                norm_first=True,
            )
        )

        self.temporal_encoder = (
            nn.TransformerEncoder(
                encoder_layer,
                num_layers=self.config.num_layers,
            )
        )

        # ------------------------------------------------------------------
        # Temporal pooling
        # ------------------------------------------------------------------

        self.temporal_pooling = (
            TemporalAttentionPooling(
                self.config.hidden_dim
            )
        )

        # ------------------------------------------------------------------
        # Current state head
        # ------------------------------------------------------------------

        self.current_state_head = (
            nn.Sequential(
                nn.Linear(
                    self.config.hidden_dim,
                    self.config.output_dim,
                ),
                nn.LayerNorm(
                    self.config.output_dim
                ),
                nn.GELU(),
            )
        )

        # ------------------------------------------------------------------
        # Trend head
        # ------------------------------------------------------------------

        self.trend_head = nn.Sequential(
            nn.Linear(
                self.config.hidden_dim,
                self.config.output_dim,
            ),
            nn.LayerNorm(
                self.config.output_dim
            ),
            nn.GELU(),
        )

        # ------------------------------------------------------------------
        # Future-state prediction
        # ------------------------------------------------------------------

        self.future_head = nn.Sequential(
            nn.Linear(
                self.config.hidden_dim
                + self.config.output_dim,
                self.config.hidden_dim,
            ),
            nn.GELU(),
            nn.Dropout(
                self.config.dropout
            ),
            nn.Linear(
                self.config.hidden_dim,
                (
                    self.config.future_steps
                    * self.config.output_dim
                ),
            ),
        )

        # ------------------------------------------------------------------
        # Uncertainty head
        # ------------------------------------------------------------------

        self.uncertainty_head = nn.Sequential(
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
    # Input validation
    # ========================================================================

    def _validate_input(
        self,
        x: torch.Tensor,
    ) -> None:
        """
        Validate longitudinal input tensor.
        """

        if x.ndim != 3:
            raise ValueError(
                "Input must have shape "
                "[batch, time, features]."
            )

        if x.shape[-1] != (
            self.config.input_dim
        ):
            raise ValueError(
                "Unexpected feature dimension. "
                f"Expected {self.config.input_dim}, "
                f"got {x.shape[-1]}."
            )

        if x.shape[1] > (
            self.config.max_timepoints
        ):
            raise ValueError(
                "Number of timepoints exceeds "
                "max_timepoints."
            )

    # ========================================================================
    # Forward
    # ========================================================================

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.

        Parameters
        ----------
        x:
            Longitudinal embeddings.

            Shape:

                [batch, time, input_dim]

        mask:
            Boolean mask:

                [batch, time]

            True = valid observation
            False = missing/padded observation.

        Returns
        -------
        dict
            Model outputs.
        """

        self._validate_input(
            x
        )

        # ------------------------------------------------------------------
        # Input projection
        # ------------------------------------------------------------------

        projected = self.input_projection(
            x
        )

        # ------------------------------------------------------------------
        # Temporal positional information
        # ------------------------------------------------------------------

        projected = self.temporal_position(
            projected
        )

        # ------------------------------------------------------------------
        # Explicit temporal differences
        # ------------------------------------------------------------------

        differences = (
            self.difference_encoder(
                projected
            )
        )

        # Combine state + change information.
        temporal_features = (
            projected
            + differences
        )

        # ------------------------------------------------------------------
        # Transformer
        # ------------------------------------------------------------------

        # Transformer expects:
        #
        #     src_key_padding_mask
        #
        # where:
        #
        #     True = ignore
        #     False = valid
        #
        padding_mask = None

        if mask is not None:

            padding_mask = ~mask

        encoded = self.temporal_encoder(
            temporal_features,
            src_key_padding_mask=padding_mask,
        )

        # ------------------------------------------------------------------
        # Temporal pooling
        # ------------------------------------------------------------------

        pooled, attention = (
            self.temporal_pooling(
                encoded,
                mask=mask,
            )
        )

        # ------------------------------------------------------------------
        # Current state
        # ------------------------------------------------------------------

        current_state = (
            self.current_state_head(
                encoded[:, -1, :]
            )
        )

        # ------------------------------------------------------------------
        # Temporal trend
        # ------------------------------------------------------------------

        trend = self.trend_head(
            pooled
        )

        # ------------------------------------------------------------------
        # Future prediction
        # ------------------------------------------------------------------

        future_input = torch.cat(
            [
                pooled,
                trend,
            ],
            dim=-1,
        )

        future_flat = self.future_head(
            future_input
        )

        future_state = future_flat.view(
            x.shape[0],
            self.config.future_steps,
            self.config.output_dim,
        )

        # ------------------------------------------------------------------
        # Uncertainty
        # ------------------------------------------------------------------

        uncertainty_logits = (
            self.uncertainty_head(
                pooled
            )
        )

        uncertainty = F.softplus(
            uncertainty_logits
        )

        return {
            "temporal_embeddings": encoded,
            "current_state": current_state,
            "temporal_trend": trend,
            "future_state": future_state,
            "uncertainty": uncertainty,
            "temporal_attention": attention,
            "pooled_state": pooled,
        }

    # ========================================================================
    # Prediction
    # ========================================================================

    @torch.no_grad()
    def predict(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Inference wrapper.
        """

        was_training = self.training

        self.eval()

        output = self.forward(
            x,
            mask=mask,
        )

        if was_training:
            self.train()

        return output

    # ========================================================================
    # Change analysis
    # ========================================================================

    @torch.no_grad()
    def compute_changes(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Calculate changes between consecutive observations.

        Returns
        -------
        dict
            absolute and normalized temporal changes.
        """

        self._validate_input(
            x
        )

        if x.shape[1] < 2:
            raise ValueError(
                "At least two timepoints are required "
                "to calculate temporal changes."
            )

        delta = (
            x[:, 1:, :]
            - x[:, :-1, :]
        )

        absolute_change = delta.abs()

        magnitude = torch.norm(
            delta,
            dim=-1,
        )

        return {
            "delta": delta,
            "absolute_change": (
                absolute_change
            ),
            "change_magnitude": magnitude,
        }

    # ========================================================================
    # Temporal trend direction
    # ========================================================================

    @torch.no_grad()
    def trend_direction(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Estimate whether the embedding is moving positively or negatively
        along its temporal trajectory.

        This is an embedding-space direction, not a clinical interpretation.
        """

        changes = self.compute_changes(
            x
        )

        delta = changes[
            "delta"
        ]

        positive = (
            torch.clamp(
                delta,
                min=0.0,
            ).mean(dim=-1)
        )

        negative = (
            torch.clamp(
                -delta,
                min=0.0,
            ).mean(dim=-1)
        )

        return {
            "positive_change": positive,
            "negative_change": negative,
        }

    # ========================================================================
    # Missing timepoints
    # ========================================================================

    @staticmethod
    def create_temporal_mask(
        batch_size: int,
        timepoints: int,
        valid_lengths: Sequence[int],
        device: Optional[
            torch.device
        ] = None,
    ) -> torch.Tensor:
        """
        Create a boolean temporal mask.

        Example
        -------

        valid_lengths = [4, 3, 2]

        creates:

            [
                [T,T,T,T],
                [T,T,T,F],
                [T,T,F,F],
            ]
        """

        if len(valid_lengths) != (
            batch_size
        ):
            raise ValueError(
                "valid_lengths must have "
                "batch_size elements."
            )

        mask = torch.zeros(
            batch_size,
            timepoints,
            dtype=torch.bool,
            device=device,
        )

        for index, length in enumerate(
            valid_lengths
        ):

            if length < 0:
                raise ValueError(
                    "Temporal length cannot "
                    "be negative."
                )

            if length > timepoints:
                raise ValueError(
                    "Temporal length exceeds "
                    "timepoints."
                )

            mask[
                index,
                :length,
            ] = True

        return mask

    # ========================================================================
    # Freeze / unfreeze
    # ========================================================================

    def freeze_temporal_encoder(
        self,
    ) -> None:
        """
        Freeze Transformer temporal encoder.
        """

        for parameter in (
            self.temporal_encoder.parameters()
        ):
            parameter.requires_grad = False

    def unfreeze_temporal_encoder(
        self,
    ) -> None:
        """
        Unfreeze Transformer temporal encoder.
        """

        for parameter in (
            self.temporal_encoder.parameters()
        ):
            parameter.requires_grad = True

    # ========================================================================
    # Checkpoint
    # ========================================================================

    def save_checkpoint(
        self,
        path: str,
        optimizer: Optional[
            torch.optim.Optimizer
        ] = None,
        epoch: Optional[int] = None,
        loss: Optional[float] = None,
    ) -> None:
        """
        Save model checkpoint.
        """

        checkpoint = {
            "model_state_dict": (
                self.state_dict()
            ),
            "config": self.config.__dict__,
        }

        if optimizer is not None:
            checkpoint[
                "optimizer_state_dict"
            ] = optimizer.state_dict()

        if epoch is not None:
            checkpoint[
                "epoch"
            ] = epoch

        if loss is not None:
            checkpoint[
                "loss"
            ] = loss

        torch.save(
            checkpoint,
            path,
        )

    def load_checkpoint(
        self,
        path: str,
        optimizer: Optional[
            torch.optim.Optimizer
        ] = None,
        strict: bool = True,
    ) -> Dict[str, object]:
        """
        Load model checkpoint.
        """

        checkpoint = torch.load(
            path,
            map_location="cpu",
        )

        if (
            isinstance(
                checkpoint,
                Mapping,
            )
            and "model_state_dict"
            in checkpoint
        ):

            self.load_state_dict(
                checkpoint[
                    "model_state_dict"
                ],
                strict=strict,
            )

            if (
                optimizer is not None
                and "optimizer_state_dict"
                in checkpoint
            ):

                optimizer.load_state_dict(
                    checkpoint[
                        "optimizer_state_dict"
                    ]
                )

            return dict(
                checkpoint
            )

        # Support plain state_dict.
        self.load_state_dict(
            checkpoint,
            strict=strict,
        )

        return {
            "model_state_dict": checkpoint
        }


# ============================================================================
# Losses
# ============================================================================


class LongitudinalStateLoss(
    nn.Module
):
    """
    Loss for future-state prediction.

    Uses Smooth L1 loss because embeddings can contain occasional
    large deviations.

    Parameters
    ----------
    reduction:
        "mean", "sum" or "none".
    """

    def __init__(
        self,
        reduction: str = "mean",
    ) -> None:
        super().__init__()

        self.loss = nn.SmoothL1Loss(
            reduction=reduction
        )

    def forward(
        self,
        predicted: torch.Tensor,
        target: torch.Tensor,
    ) -> torch.Tensor:

        if predicted.shape != (
            target.shape
        ):
            raise ValueError(
                "Predicted and target "
                "shapes must match."
            )

        return self.loss(
            predicted,
            target,
        )


class LongitudinalCombinedLoss(
    nn.Module
):
    """
    Combined loss for:

        future-state prediction
        temporal trend consistency
    """

    def __init__(
        self,
        future_weight: float = 1.0,
        trend_weight: float = 0.25,
    ) -> None:
        super().__init__()

        self.future_weight = (
            future_weight
        )

        self.trend_weight = (
            trend_weight
        )

        self.state_loss = (
            nn.SmoothL1Loss()
        )

    def forward(
        self,
        predicted_future: torch.Tensor,
        target_future: torch.Tensor,
        predicted_trend: Optional[
            torch.Tensor
        ] = None,
        target_trend: Optional[
            torch.Tensor
        ] = None,
    ) -> torch.Tensor:

        future_loss = (
            self.state_loss(
                predicted_future,
                target_future,
            )
        )

        total = (
            self.future_weight
            * future_loss
        )

        if (
            predicted_trend is not None
            and target_trend is not None
        ):

            trend_loss = (
                self.state_loss(
                    predicted_trend,
                    target_trend,
                )
            )

            total = (
                total
                + self.trend_weight
                * trend_loss
            )

        return total


# ============================================================================
# Utility functions
# ============================================================================


def stack_temporal_states(
    states: Sequence[torch.Tensor],
) -> torch.Tensor:
    """
    Stack individual timepoint embeddings.

    Input
    -----

        [
            [batch, features],  # T0
            [batch, features],  # T1
            [batch, features],  # T2
            [batch, features],  # T3
        ]

    Output
    ------

        [batch, time, features]
    """

    if not states:
        raise ValueError(
            "At least one state is required."
        )

    first_shape = states[0].shape

    if len(first_shape) != 2:
        raise ValueError(
            "Each state must have shape "
            "[batch, features]."
        )

    for state in states:

        if state.shape != first_shape:
            raise ValueError(
                "All temporal states must "
                "have identical shapes."
            )

    return torch.stack(
        states,
        dim=1,
    )


def temporal_labels(
    num_timepoints: int,
) -> List[str]:
    """
    Generate standard temporal labels.

    Example:

        4 -> ["T0", "T1", "T2", "T3"]
    """

    if num_timepoints <= 0:
        raise ValueError(
            "num_timepoints must be positive."
        )

    return [
        f"T{i}"
        for i in range(
            num_timepoints
        )
    ]


# ============================================================================
# Model factory
# ============================================================================


def create_longitudinal_model(
    config: Optional[
        LongitudinalModelConfig
    ] = None,
    checkpoint: Optional[str] = None,
    device: Optional[str] = None,
) -> LongitudinalModel:
    """
    Create longitudinal model.
    """

    model = LongitudinalModel(
        config=config
    )

    if checkpoint is not None:

        model.load_checkpoint(
            checkpoint,
            strict=False,
        )

    if device is not None:

        model = model.to(
            device
        )

    return model


# ============================================================================
# Example
# ============================================================================


if __name__ == "__main__":

    # ------------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------------

    config = (
        LongitudinalModelConfig(
            input_dim=256,
            hidden_dim=256,
            num_heads=8,
            num_layers=4,
            feedforward_dim=1024,
            max_timepoints=16,
            future_steps=1,
            output_dim=256,
        )
    )

    # ------------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------------

    model = LongitudinalModel(
        config
    )

    # ------------------------------------------------------------------------
    # Example T0-T3 data
    # ------------------------------------------------------------------------

    batch_size = 4

    T0 = torch.randn(
        batch_size,
        config.input_dim,
    )

    T1 = torch.randn(
        batch_size,
        config.input_dim,
    )

    T2 = torch.randn(
        batch_size,
        config.input_dim,
    )

    T3 = torch.randn(
        batch_size,
        config.input_dim,
    )

    # ------------------------------------------------------------------------
    # Stack temporal observations
    # ------------------------------------------------------------------------

    temporal_data = (
        stack_temporal_states(
            [
                T0,
                T1,
                T2,
                T3,
            ]
        )
    )

    print(
        "Temporal data:",
        temporal_data.shape,
    )

    # Expected:
    #
    # [4, 4, 256]

    # ------------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------------

    output = model.predict(
        temporal_data
    )

    print(
        "Encoded temporal states:",
        output[
            "temporal_embeddings"
        ].shape,
    )

    print(
        "Current state:",
        output[
            "current_state"
        ].shape,
    )

    print(
        "Temporal trend:",
        output[
            "temporal_trend"
        ].shape,
    )

    print(
        "Future state:",
        output[
            "future_state"
        ].shape,
    )

    print(
        "Uncertainty:",
        output[
            "uncertainty"
        ].shape,
    )

    print(
        "Temporal attention:",
        output[
            "temporal_attention"
        ].shape,
    )

    # ------------------------------------------------------------------------
    # Temporal changes
    # ------------------------------------------------------------------------

    changes = (
        model.compute_changes(
            temporal_data
        )
    )

    print(
        "\nChange magnitudes:",
        changes[
            "change_magnitude"
        ],
    )

    # ------------------------------------------------------------------------
    # Trend direction
    # ------------------------------------------------------------------------

    trend = (
        model.trend_direction(
            temporal_data
        )
    )

    print(
        "\nPositive change:",
        trend[
            "positive_change"
        ],
    )

    print(
        "\nNegative change:",
        trend[
            "negative_change"
        ],
    )

    # ------------------------------------------------------------------------
    # Example with missing T3
    # ------------------------------------------------------------------------

    mask = (
        model.create_temporal_mask(
            batch_size=batch_size,
            timepoints=4,
            valid_lengths=[
                4,
                3,
                4,
                2,
            ],
        )
    )

    output_masked = model.predict(
        temporal_data,
        mask=mask,
    )

    print(
        "\nTemporal mask:"
    )

    print(
        mask
    )

    print(
        "\nMasked future prediction:",
        output_masked[
            "future_state"
        ].shape,
    )