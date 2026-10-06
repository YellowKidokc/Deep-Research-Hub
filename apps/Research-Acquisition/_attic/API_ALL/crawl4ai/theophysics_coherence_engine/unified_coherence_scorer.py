#!/usr/bin/env python3
"""
UnifiedCoherenceScorer - Bridge to Fruits of the Spirit Scorer

This adapter makes fruits_scorer.py compatible with chi_delta_grace_pipeline.py.

It provides the interface expected by the pipeline while using the
audited 12-fruit structural invariants system.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add fruits_scorer to path
sys.path.insert(0, r'O:\Theophysics_Backend\In_House_Programs\Plugins\Theophysics theory downloader\Data_Analytics\Scripts')

from fruits_scorer import analyze_theory_fruits, FruitsAnalysis


class UnifiedCoherenceScorer:
    """
    Bridge between chi_delta_grace_pipeline and fruits_scorer.
    
    Provides χ (coherence) from Fruits of the Spirit metrics:
    - F1-Grace through F12-Joy
    - Each ranges -1 to +1
    - Sum ranges -12 to +12
    - Normalized to 0-1 for χ
    """
    
    def __init__(self, rubrics_dir: str = None):
        """
        Initialize scorer.
        
        Args:
            rubrics_dir: Not used (fruits_scorer has built-in patterns)
        """
        self.rubrics_dir = rubrics_dir
        self.version = "fruits_12_v1"
    
    def score_text(self, text: str, doc_id: str = "unknown") -> Dict[str, Any]:
        """
        Score text using Fruits of the Spirit metrics.
        
        Args:
            text: Document text to analyze
            doc_id: Optional identifier for tracking
            
        Returns:
            Dictionary with:
            - chi (χ): Overall coherence [0, 1]
            - Individual fruit scores
            - Metadata
        """
        # Run fruits analysis
        analysis: FruitsAnalysis = analyze_theory_fruits(text, doc_id)
        
        # Normalize total score from [-12, +12] to [0, 1]
        chi = (analysis.total_score + 12) / 24
        chi = max(0.0, min(1.0, chi))  # Clamp to valid range
        
        # Build result dictionary
        result = {
            # Main output (required by pipeline)
            "chi": chi,
            "χ": chi,  # Greek letter alias
            "coherence": chi,  # English alias
            
            # Raw scores
            "total_score": analysis.total_score,
            "normalized_score": analysis.normalized_score,
            "grade": analysis.grade,
            "interpretation": analysis.interpretation,
            
            # Individual fruits (for diagnostics)
            "f1_grace": analysis.f1_grace.score,
            "f2_hope": analysis.f2_hope.score,
            "f3_patience": analysis.f3_patience.score,
            "f4_faithfulness": analysis.f4_faithfulness.score,
            "f5_self_control": analysis.f5_self_control.score,
            "f6_love": analysis.f6_love.score,
            "f7_peace": analysis.f7_peace.score,
            "f8_truth": analysis.f8_truth.score,
            "f9_humility": analysis.f9_humility.score,
            "f10_goodness": analysis.f10_goodness.score,
            "f11_unity": analysis.f11_unity.score,
            "f12_joy": analysis.f12_joy.score,
            
            # Metadata
            "word_count": analysis.word_count,
            "scorer_version": self.version,
        }
        
        return result
    
    def score(self, text: str, **kwargs) -> Dict[str, Any]:
        """Alias for score_text (for compatibility)."""
        doc_id = kwargs.get('doc_id', 'unknown')
        return self.score_text(text, doc_id)
    
    def get_fruit_breakdown(self, text: str) -> Dict[str, float]:
        """
        Get detailed breakdown of fruit scores.
        
        Useful for diagnostics: "which fruits are declining?"
        
        Returns:
            Dict mapping fruit names to scores [-1, +1]
        """
        analysis = analyze_theory_fruits(text, "breakdown")
        
        return {
            "grace": analysis.f1_grace.score,
            "hope": analysis.f2_hope.score,
            "patience": analysis.f3_patience.score,
            "faithfulness": analysis.f4_faithfulness.score,
            "self_control": analysis.f5_self_control.score,
            "love": analysis.f6_love.score,
            "peace": analysis.f7_peace.score,
            "truth": analysis.f8_truth.score,
            "humility": analysis.f9_humility.score,
            "goodness": analysis.f10_goodness.score,
            "unity": analysis.f11_unity.score,
            "joy": analysis.f12_joy.score,
        }


# Backward compatibility aliases
class CoherenceScorer(UnifiedCoherenceScorer):
    """Alias for backward compatibility."""
    pass


def score_text_simple(text: str) -> float:
    """
    Simplified interface: just return χ.
    
    Args:
        text: Text to score
        
    Returns:
        χ (coherence) in [0, 1]
    """
    scorer = UnifiedCoherenceScorer()
    result = scorer.score_text(text)
    return result['chi']


if __name__ == "__main__":
    # Quick test
    test_text = """
    This is a test document. It promotes cooperation, love, and truth.
    The community works together to solve problems patiently.
    They maintain their core values while adapting to new evidence.
    There is hope for the future and grace for mistakes.
    """
    
    scorer = UnifiedCoherenceScorer()
    result = scorer.score_text(test_text, "test_doc")
    
    print("=" * 60)
    print("UnifiedCoherenceScorer Test")
    print("=" * 60)
    print(f"Chi (coherence): {result['chi']:.4f}")
    print(f"Grade: {result['grade']}")
    print(f"Interpretation: {result['interpretation']}")
    print()
    print("Fruit breakdown:")
    for i in range(1, 13):
        fruit_key = f"f{i}_" + ["grace", "hope", "patience", "faithfulness", 
                                 "self_control", "love", "peace", "truth",
                                 "humility", "goodness", "unity", "joy"][i-1]
        print(f"  {fruit_key:20s}: {result[fruit_key]:+.3f}")
    print("=" * 60)
