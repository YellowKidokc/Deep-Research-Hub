#!/usr/bin/env python3
"""
MINIMAL WORKING EXAMPLE
=======================

Demonstrates the Coherence Engine on a simple test case.
"""

from unified_scorer import CoherenceEngine
from core import Entity, ClaimSet, Observations


def create_test_entity():
    """Create a minimal test entity for demonstration."""
    
    # Create entity
    entity = Entity(
        entity_id="usa_1970_2020",
        entity_type="nation",
        name="United States (1970-2020)",
        description="Test case using public data"
    )
    
    # Define what the entity claims (from founding documents)
    entity.claims = ClaimSet(
        entity_id="usa_1970_2020",
        source_texts=[
            "US Constitution",
            "Declaration of Independence"
        ],
        extracted_claims=[
            "equal protection under law",
            "promote general welfare",
            "secure the blessings of liberty"
        ],
        claim_categories={
            "constitutional": ["equal protection", "secure liberty"],
            "welfare": ["promote general welfare"]
        }
    )
    
    # Define what we observe (real measurable data)
    entity.observations = Observations(
        entity_id="usa_1970_2020",
        time_series={
            # Corruption Perception Index (Transparency International)
            # Higher = less corrupt
            "corruption_index": [
                (1980, 75.0),
                (1985, 74.5),
                (1990, 73.0),
                (1995, 76.0),
                (2000, 76.0),
                (2005, 75.0),
                (2010, 71.0),
                (2015, 73.0),
                (2020, 67.0)
            ],
            
            # Trust in institutions (General Social Survey)
            # Fraction of population trusting
            "trust_index": [
                (1980, 0.45),
                (1985, 0.43),
                (1990, 0.40),
                (1995, 0.38),
                (2000, 0.35),
                (2005, 0.34),
                (2010, 0.32),
                (2015, 0.30),
                (2020, 0.29)
            ],
            
            # Marriage rate (per 1000 population)
            "marriage_rate": [
                (1980, 10.6),
                (1985, 10.1),
                (1990, 9.8),
                (1995, 8.9),
                (2000, 8.2),
                (2005, 7.6),
                (2010, 6.8),
                (2015, 6.9),
                (2020, 6.5)
            ]
        },
        events=[
            # Example events for grace classification
            {"year": 1991, "type": "war", "description": "Gulf War"},
            {"year": 2001, "type": "crisis", "description": "9/11 attacks"},
            {"year": 2008, "type": "crisis", "description": "Financial crisis"}
        ],
        data_sources={
            "corruption_index": "Transparency International CPI",
            "trust_index": "General Social Survey",
            "marriage_rate": "CDC National Center for Health Statistics"
        }
    )
    
    return entity


def main():
    """Run the minimal example."""
    
    print("=" * 70)
    print("THEOPHYSICS COHERENCE ENGINE - Minimal Example")
    print("=" * 70)
    print()
    
    # Create test entity
    print("Creating test entity...")
    entity = create_test_entity()
    
    # Validate
    is_valid, msg = entity.validate()
    print(f"Entity validation: {msg}")
    print()
    
    # Initialize engine
    print("Initializing Coherence Engine...")
    engine = CoherenceEngine(
        model_version="minimal_v1",
        output_dir="outputs/manifests"
    )
    print()
    
    # Run analysis
    print("Running analysis (this may take a moment)...")
    print()
    
    result = engine.run(entity, use_minimal=True)
    
    # Display results
    print()
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print()
    
    print(f"Entity: {entity.name}")
    print(f"Time period: {entity.observations.get_time_range()}")
    print()
    
    print("χ (Coherence):")
    print(f"  Mean: {result.diagnostics['chi_mean']:.3f}")
    print(f"  Trend: {result.diagnostics['chi_trend']:.4f} per year")
    if result.diagnostics['chi_trend'] < -0.01:
        print("  ⚠️  Declining coherence detected")
    elif result.diagnostics['chi_trend'] > 0.01:
        print("  ✓ Improving coherence")
    else:
        print("  → Stable")
    print()
    
    print("δ (Drift):")
    print(f"  Mean: {result.diagnostics['drift_mean']:.3f}")
    if result.diagnostics['drift_mean'] > 0.5:
        print("  ⚠️  High entropy pressure")
    elif result.diagnostics['drift_mean'] > 0.2:
        print("  ⚠  Moderate drift")
    else:
        print("  ✓ Stable")
    print()
    
    print("G (Grace Events):")
    print(f"  Detected: {result.diagnostics['grace_events_count']}")
    if result.diagnostics['grace_events_count'] > 0:
        print("  → Exogenous impulses detected (see manifest for details)")
    print()
    
    # Show a few data points
    print("Sample data points:")
    print()
    print("Year  |   χ   |   δ   |   G   ")
    print("------|-------|-------|-------")
    for i in range(min(5, len(result.chi_scores))):
        year_chi = result.chi_scores[i]
        year_drift = result.drift_scores[i] if i < len(result.drift_scores) else (0, 0)
        year_grace = result.grace_scores[i] if i < len(result.grace_scores) else (0, 0)
        
        print(f"{year_chi[0]:4d}  | {year_chi[1]:5.3f} | {year_drift[1]:5.3f} | {year_grace[1]:+5.3f}")
    
    if len(result.chi_scores) > 5:
        print("...")
        last = len(result.chi_scores) - 1
        year_chi = result.chi_scores[last]
        year_drift = result.drift_scores[last] if last < len(result.drift_scores) else (0, 0)
        year_grace = result.grace_scores[last] if last < len(result.grace_scores) else (0, 0)
        print(f"{year_chi[0]:4d}  | {year_chi[1]:5.3f} | {year_drift[1]:5.3f} | {year_grace[1]:+5.3f}")
    
    print()
    print("=" * 70)
    print("Full results saved to manifest (JSON)")
    print(f"Run ID: {result.run_id}")
    print("=" * 70)


if __name__ == "__main__":
    main()
