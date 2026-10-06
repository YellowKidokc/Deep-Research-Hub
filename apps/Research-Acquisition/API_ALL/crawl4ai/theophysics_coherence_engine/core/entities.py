"""
Core entity definitions for the Theophysics Coherence Engine.
These represent systems (nations, religions, institutions) under analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import json


@dataclass
class ClaimSet:
    """
    Declared axioms, purpose, and claims of an entity.
    
    Examples:
    - For religions: creeds, commandments, core doctrines
    - For nations: constitution, founding documents, stated principles
    - For institutions: charter, mission statement, published standards
    """
    entity_id: str
    source_texts: List[str]  # Paths to source documents
    extracted_claims: List[str]  # Key claims extracted
    claim_categories: Dict[str, List[str]]  # e.g., {"moral": [...], "economic": [...]}
    extraction_date: datetime = field(default_factory=datetime.now)
    
    def to_hash(self) -> str:
        """Generate deterministic hash for auditability."""
        content = json.dumps({
            "entity_id": self.entity_id,
            "claims": sorted(self.extracted_claims),
            "categories": {k: sorted(v) for k, v in sorted(self.claim_categories.items())}
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass
class Observations:
    """
    Time series data and measurable outputs for an entity.
    
    Must be deterministic and reproducible.
    All sources must be documented.
    """
    entity_id: str
    time_series: Dict[str, List[tuple]]  # e.g., {"corruption_index": [(year, value), ...]}
    events: List[Dict[str, Any]]  # Discrete events with timestamps
    data_sources: Dict[str, str]  # Metric -> source URL/citation
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_hash(self) -> str:
        """Generate deterministic hash for dataset version."""
        content = json.dumps({
            "entity_id": self.entity_id,
            "series_keys": sorted(self.time_series.keys()),
            "event_count": len(self.events),
            "sources": sorted(self.data_sources.values())
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def get_time_range(self) -> tuple:
        """Get (min_year, max_year) covered by observations."""
        all_years = []
        for series in self.time_series.values():
            all_years.extend([t[0] for t in series])
        if not all_years:
            return (None, None)
        return (min(all_years), max(all_years))


@dataclass
class Entity:
    """
    A system being analyzed (nation, religion, institution, etc).
    
    Bundles together:
    - What it claims (ClaimSet)
    - What it does (Observations)
    - Metadata for tracking
    """
    entity_id: str
    entity_type: str  # "nation", "religion", "institution", etc.
    name: str
    description: str
    
    claims: Optional[ClaimSet] = None
    observations: Optional[Observations] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> tuple:
        """
        Check if entity is ready for analysis.
        Returns (is_valid, error_message).
        """
        if not self.claims:
            return (False, "No ClaimSet defined")
        if not self.observations:
            return (False, "No Observations defined")
        if not self.observations.time_series:
            return (False, "No time series data")
        
        return (True, "Valid")
    
    def summary(self) -> Dict[str, Any]:
        """Generate summary for logging/manifests."""
        time_range = self.observations.get_time_range() if self.observations else (None, None)
        
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "type": self.entity_type,
            "time_range": time_range,
            "claims_hash": self.claims.to_hash() if self.claims else None,
            "observations_hash": self.observations.to_hash() if self.observations else None,
            "is_valid": self.validate()[0]
        }


@dataclass
class ModelSpec:
    """
    Specification of how χ, δ, G are computed.
    
    This is versioned and locked per run for auditability.
    """
    version: str
    chi_method: str  # "fruits_12", "fruits_minimal", etc.
    drift_method: str  # "minimal_v1", "var_model", etc.
    grace_method: str  # "residual_v1", "changepoint_v2", etc.
    
    parameters: Dict[str, Any] = field(default_factory=dict)
    rubric_hashes: Dict[str, str] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_hash(self) -> str:
        """Generate hash of model configuration."""
        content = json.dumps({
            "version": self.version,
            "chi_method": self.chi_method,
            "drift_method": self.drift_method,
            "grace_method": self.grace_method,
            "parameters": self.parameters,
            "rubric_hashes": self.rubric_hashes
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass
class RunResult:
    """
    Complete output of a single scoring run.
    
    Includes all inputs, outputs, and provenance for full auditability.
    """
    run_id: str
    entity: Entity
    model_spec: ModelSpec
    
    # Core outputs
    chi_scores: List[tuple]  # [(year, chi), ...]
    drift_scores: List[tuple]  # [(year, delta), ...]
    grace_scores: List[tuple]  # [(year, G), ...]
    
    # Diagnostics
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    # Provenance
    timestamp: datetime = field(default_factory=datetime.now)
    runtime_seconds: float = 0.0
    
    def to_manifest(self) -> Dict[str, Any]:
        """
        Generate complete run manifest for auditability.
        Anyone can rerun with this manifest and verify results.
        """
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "runtime_seconds": self.runtime_seconds,
            
            "entity": self.entity.summary(),
            "model_spec": {
                "version": self.model_spec.version,
                "model_hash": self.model_spec.to_hash(),
                "chi_method": self.model_spec.chi_method,
                "drift_method": self.model_spec.drift_method,
                "grace_method": self.model_spec.grace_method,
                "parameters": self.model_spec.parameters,
                "rubric_hashes": self.model_spec.rubric_hashes
            },
            
            "outputs": {
                "chi_scores": self.chi_scores,
                "drift_scores": self.drift_scores,
                "grace_scores": self.grace_scores
            },
            
            "diagnostics": self.diagnostics,
            "warnings": self.warnings
        }
    
    def save_manifest(self, output_dir: str):
        """Save run manifest to JSON."""
        import pathlib
        output_path = pathlib.Path(output_dir) / f"manifest_{self.run_id}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_manifest(), f, indent=2, default=str)
        
        return output_path
