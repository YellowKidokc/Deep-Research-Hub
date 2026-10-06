"""
Drift Scorer (δ): Internal misalignment + decay pressure

δ(t) = w₁ · misalignment(t) + w₂ · decoherence_pressure(t)

MINIMAL VERSION (auditable, non-circular):
- δ₁ (misalignment): claimed purpose vs observed outputs
- δ₂ (pressure): trend loss rate + volatility + correction failure
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DriftScore:
    """Complete drift measurement for a time point."""
    year: int
    delta_total: float  # Combined drift
    delta_1_misalignment: float  # Claim vs reality gap
    delta_2_pressure: float  # Entropy pressure
    
    # Components for δ₂
    trend_loss_rate: float
    volatility: float
    correction_failure: float
    
    interpretation: str


class DriftScorer:
    """
    Compute drift δ(t) from entity data.
    
    Minimal implementation:
    δ(t) = max(0, -Δχ/Δt) + misalignment_score
    
    Where:
    - Δχ/Δt negative = coherence declining = drift
    - misalignment = gap between claims and observed metrics
    """
    
    def __init__(self, w_misalignment: float = 0.5, w_pressure: float = 0.5):
        """
        Initialize with weights for drift components.
        
        Args:
            w_misalignment: Weight for δ₁ (claim-reality gap)
            w_pressure: Weight for δ₂ (entropy pressure)
        """
        self.w1 = w_misalignment
        self.w2 = w_pressure
        
    def compute_drift(self,
                     chi_scores: List[Tuple[int, float]],
                     observations: Dict[str, List[Tuple[int, float]]],
                     claim_metrics: Dict[str, float]) -> List[DriftScore]:
        """
        Compute drift scores for all time points.
        
        Args:
            chi_scores: [(year, chi), ...] coherence time series
            observations: {metric_name: [(year, value), ...]}
            claim_metrics: {metric_name: expected_value} from ClaimSet
            
        Returns:
            List of DriftScore objects, one per year
        """
        results = []
        
        for i, (year, chi) in enumerate(chi_scores):
            # Compute δ₁: misalignment
            delta_1 = self._compute_misalignment(year, observations, claim_metrics)
            
            # Compute δ₂: decoherence pressure (needs historical context)
            if i >= 3:  # Need at least 3 years for trend
                window = chi_scores[max(0, i-5):i+1]  # Rolling 5-year window
                delta_2, trend, vol, corr_fail = self._compute_pressure(window)
            else:
                delta_2, trend, vol, corr_fail = 0.0, 0.0, 0.0, 0.0
            
            # Combined drift
            delta_total = self.w1 * delta_1 + self.w2 * delta_2
            
            # Interpretation
            if delta_total > 0.5:
                interp = "High entropy pressure - system degrading"
            elif delta_total > 0.2:
                interp = "Moderate drift - needs correction"
            elif delta_total > 0:
                interp = "Minor drift detected"
            else:
                interp = "No drift - stable or improving"
            
            results.append(DriftScore(
                year=year,
                delta_total=delta_total,
                delta_1_misalignment=delta_1,
                delta_2_pressure=delta_2,
                trend_loss_rate=trend,
                volatility=vol,
                correction_failure=corr_fail,
                interpretation=interp
            ))
        
        return results
    
    def _compute_misalignment(self,
                             year: int,
                             observations: Dict[str, List[Tuple]],
                             claims: Dict[str, float]) -> float:
        """
        δ₁: Measure gap between claimed values and observed reality.
        
        For each metric:
        - Compare observed value to claimed/expected value
        - Normalize to [0, 1] range
        - Average across all metrics
        
        Returns:
            misalignment score (0 = perfect match, 1 = total mismatch)
        """
        if not claims:
            return 0.0
        
        gaps = []
        
        for metric_name, expected in claims.items():
            if metric_name not in observations:
                continue
            
            # Find observed value for this year
            metric_series = observations[metric_name]
            year_values = [v for y, v in metric_series if y == year]
            
            if not year_values:
                continue
            
            observed = year_values[0]
            
            # Compute normalized gap
            # Assumes higher = better for most metrics
            # TODO: Make this configurable per metric in rubric
            gap = abs(expected - observed) / (abs(expected) + 1e-6)
            gap = min(1.0, gap)  # Cap at 1.0
            
            gaps.append(gap)
        
        return np.mean(gaps) if gaps else 0.0
    
    def _compute_pressure(self,
                         chi_window: List[Tuple[int, float]]) -> Tuple[float, float, float, float]:
        """
        δ₂: Compute decoherence pressure from χ dynamics.
        
        Three components:
        1. Trend loss rate: slope of χ (negative = declining)
        2. Volatility: variance of χ (high = fragile)
        3. Correction failure: attempts to fix don't change slope
        
        Returns:
            (combined_pressure, trend_component, volatility_component, correction_component)
        """
        years = [y for y, _ in chi_window]
        chi_vals = [c for _, c in chi_window]
        
        if len(chi_vals) < 2:
            return 0.0, 0.0, 0.0, 0.0
        
        # 1. Trend loss rate (negative slope = pressure)
        # Simple linear fit
        x = np.arange(len(chi_vals))
        slope, _ = np.polyfit(x, chi_vals, 1)
        trend_loss = max(0, -slope)  # Only count declining trends
        
        # 2. Volatility (standard deviation)
        volatility = np.std(chi_vals)
        
        # 3. Correction failure (crude proxy: high volatility + declining)
        # If corrections were working, we'd see stable or rising trend
        # If we see decline despite variance, corrections are failing
        if slope < 0 and volatility > 0.1:
            correction_failure = volatility * abs(slope)
        else:
            correction_failure = 0.0
        
        # Combine components (equal weight for minimal version)
        pressure = (trend_loss + volatility + correction_failure) / 3.0
        
        # Normalize to [0, 1]
        pressure = min(1.0, pressure)
        
        return pressure, trend_loss, volatility, correction_failure


def minimal_drift(chi_scores: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
    """
    Simplest possible drift: negative change in χ.
    
    δ(t) = max(0, -Δχ/Δt)
    
    This is the absolute minimum for testing the framework.
    """
    results = []
    
    for i, (year, chi) in enumerate(chi_scores):
        if i == 0:
            drift = 0.0
        else:
            prev_chi = chi_scores[i-1][1]
            delta_chi = chi - prev_chi
            drift = max(0, -delta_chi)  # Only count declines as drift
        
        results.append((year, drift))
    
    return results
