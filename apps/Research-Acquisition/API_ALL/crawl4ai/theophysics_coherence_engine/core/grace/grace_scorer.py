"""
Grace Scorer (G): Exogenous impulse detection via residual analysis

G(t) = χ_observed(t+1) - χ_predicted(t+1)

Where prediction comes from internal dynamics model.

Grace is WHATEVER explains coherence gains that cannot be accounted 
for by the system's own dynamics.

This is auditable because:
1. We publish the prediction model f
2. We publish all inputs
3. Anyone can recompute the residual
4. We classify residuals by signature (not vibes)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class GraceType(Enum):
    """Classification of grace events by signature."""
    RESOURCE_WINDFALL = "resource_windfall"  # Aid, oil, loans, trade boom
    EXISTENTIAL_THREAT = "existential_threat"  # War, invasion, collapse pressure forcing unity
    REVIVAL = "revival"  # Rapid trust/moral rebind, voluntary behavior change
    UNKNOWN = "unknown"  # Positive residual, unclear cause
    NONE = "none"  # No grace detected


@dataclass
class GraceEvent:
    """A detected grace impulse."""
    year: int
    magnitude: float  # G value
    grace_type: GraceType
    confidence: float  # How certain is the classification?
    evidence: Dict[str, any]  # Supporting data for the classification


@dataclass
class GraceScore:
    """Complete grace measurement for a time point."""
    year: int
    G: float  # Total grace (residual)
    chi_observed: float
    chi_predicted: float
    
    event: Optional[GraceEvent]
    interpretation: str


class GraceScorer:
    """
    Detect grace as residual from internal dynamics model.
    
    Minimal implementation:
    - Predict χ(t+1) from trend of last N years
    - G = χ_observed - χ_predicted
    - Classify if |G| > threshold
    """
    
    def __init__(self, 
                 prediction_window: int = 5,
                 grace_threshold: float = 0.1,
                 classification_enabled: bool = True):
        """
        Initialize grace detector.
        
        Args:
            prediction_window: Years to use for trend prediction
            grace_threshold: Minimum |G| to count as grace event
            classification_enabled: Whether to classify grace types
        """
        self.window = prediction_window
        self.threshold = grace_threshold
        self.classify = classification_enabled
    
    def compute_grace(self,
                     chi_scores: List[Tuple[int, float]],
                     drift_scores: List[Tuple[int, float]],
                     events: Optional[List[Dict]] = None) -> List[GraceScore]:
        """
        Compute grace scores for all time points.
        
        Args:
            chi_scores: [(year, chi), ...] observed coherence
            drift_scores: [(year, delta), ...] computed drift
            events: Optional list of known external events for classification
            
        Returns:
            List of GraceScore objects
        """
        results = []
        
        for i, (year, chi_obs) in enumerate(chi_scores):
            # Need enough history for prediction
            if i < self.window:
                results.append(GraceScore(
                    year=year,
                    G=0.0,
                    chi_observed=chi_obs,
                    chi_predicted=chi_obs,
                    event=None,
                    interpretation="Insufficient history for prediction"
                ))
                continue
            
            # Predict χ from internal model
            window_data = chi_scores[i-self.window:i]
            chi_pred = self._predict_chi(window_data, drift_scores[i][1])
            
            # Compute residual (Grace)
            G = chi_obs - chi_pred
            
            # Detect and classify grace event if threshold exceeded
            event = None
            if abs(G) > self.threshold and self.classify and events:
                event = self._classify_grace(year, G, events)
            
            # Interpretation
            if G > self.threshold:
                if event and event.grace_type == GraceType.REVIVAL:
                    interp = f"Major positive impulse detected - Revival signature"
                else:
                    interp = f"Positive impulse detected - exceeds prediction by {G:.3f}"
            elif G < -self.threshold:
                interp = f"Negative shock - worse than predicted by {abs(G):.3f}"
            else:
                interp = "On trend - no exogenous impulse"
            
            results.append(GraceScore(
                year=year,
                G=G,
                chi_observed=chi_obs,
                chi_predicted=chi_pred,
                event=event,
                interpretation=interp
            ))
        
        return results
    
    def _predict_chi(self,
                    window: List[Tuple[int, float]],
                    current_drift: float) -> float:
        """
        Simple internal dynamics model for χ prediction.
        
        Minimal version:
        χ_pred = trend_extrapolation - drift_effect
        
        More advanced versions could use:
        - AR(1) or VAR models
        - Structural equation models
        - Machine learning (with cross-validation)
        
        Returns:
            Predicted χ for next time step
        """
        years = [y for y, _ in window]
        chi_vals = [c for _, c in window]
        
        # Linear trend
        x = np.arange(len(chi_vals))
        slope, intercept = np.polyfit(x, chi_vals, 1)
        
        # Extrapolate one step forward
        next_x = len(chi_vals)
        chi_trend = slope * next_x + intercept
        
        # Apply drift effect (reduces predicted χ)
        chi_pred = chi_trend - current_drift
        
        # Bound to [0, 1] if χ is normalized
        chi_pred = max(0.0, min(1.0, chi_pred))
        
        return chi_pred
    
    def _classify_grace(self,
                       year: int,
                       G: float,
                       events: List[Dict]) -> Optional[GraceEvent]:
        """
        Classify type of grace event based on signature.
        
        Uses external event data + behavioral signatures.
        
        Taxonomy:
        - Resource windfall: economic data shows sudden input
        - Existential threat: war/invasion data + unity spike
        - Revival: trust metrics + voluntary behavior + fertility
        - Unknown: positive G but no clear signature
        
        Returns:
            GraceEvent with classification, or None if no event
        """
        if abs(G) < self.threshold:
            return None
        
        # Find events near this year (±1 year window)
        relevant_events = [e for e in events 
                          if abs(e.get('year', 0) - year) <= 1]
        
        if not relevant_events:
            return GraceEvent(
                year=year,
                magnitude=G,
                grace_type=GraceType.UNKNOWN,
                confidence=0.5,
                evidence={"note": "No matching external events"}
            )
        
        # Classification logic (simplified for minimal version)
        # TODO: Make this data-driven via rubric
        
        for event in relevant_events:
            event_type = event.get('type', '').lower()
            
            # Resource windfall signature
            if 'aid' in event_type or 'loan' in event_type or 'boom' in event_type:
                return GraceEvent(
                    year=year,
                    magnitude=G,
                    grace_type=GraceType.RESOURCE_WINDFALL,
                    confidence=0.8,
                    evidence=event
                )
            
            # Existential threat signature (paradoxical positive effect)
            if 'war' in event_type or 'invasion' in event_type or 'crisis' in event_type:
                if G > 0:  # Threat that increases coherence
                    return GraceEvent(
                        year=year,
                        magnitude=G,
                        grace_type=GraceType.EXISTENTIAL_THREAT,
                        confidence=0.7,
                        evidence=event
                    )
            
            # Revival signature (requires behavioral data)
            if 'revival' in event_type or 'awakening' in event_type:
                return GraceEvent(
                    year=year,
                    magnitude=G,
                    grace_type=GraceType.REVIVAL,
                    confidence=0.9,
                    evidence=event
                )
        
        # Default: unknown positive impulse
        return GraceEvent(
            year=year,
            magnitude=G,
            grace_type=GraceType.UNKNOWN,
            confidence=0.5,
            evidence={"matched_events": len(relevant_events)}
        )


def minimal_grace(chi_scores: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
    """
    Simplest possible grace: positive change beyond trend.
    
    G(t) = max(0, Δχ - predicted_Δχ)
    
    Where predicted_Δχ comes from last N years average.
    """
    results = []
    window_size = 5
    
    for i, (year, chi) in enumerate(chi_scores):
        if i < window_size + 1:
            # Not enough history
            results.append((year, 0.0))
            continue
        
        # Compute average change over window
        window = chi_scores[i-window_size:i]
        changes = [window[j+1][1] - window[j][1] for j in range(len(window)-1)]
        avg_change = np.mean(changes)
        
        # Actual change
        actual_change = chi - chi_scores[i-1][1]
        
        # Grace = positive surprise
        grace = max(0, actual_change - avg_change)
        
        results.append((year, grace))
    
    return results
