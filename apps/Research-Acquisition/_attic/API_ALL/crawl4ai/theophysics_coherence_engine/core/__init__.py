"""
Theophysics Coherence Engine - Core Module

Provides operational, auditable, non-circular metrics for predicting
societal/institutional collapse via structural invariants.

Key Components:
- χ (coherence): Fruits of the Spirit 12-metric score
- δ (drift): Internal misalignment + entropy pressure  
- G (grace): Exogenous impulses (detected as residuals)
"""

from .entities import (
    Entity,
    ClaimSet,
    Observations,
    ModelSpec,
    RunResult
)

__all__ = [
    'Entity',
    'ClaimSet',
    'Observations',
    'ModelSpec',
    'RunResult'
]
