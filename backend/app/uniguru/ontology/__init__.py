"""Deterministic ontology backbone for UniGuru."""

from app.uniguru.ontology.exceptions import ImmutableConceptViolation, OntologyGraphValidationError
from app.uniguru.ontology.graph import OntologyGraph, get_frozen_concepts
from app.uniguru.ontology.registry import OntologyRegistry
from app.uniguru.ontology.snapshot_manager import SnapshotManager

__all__ = [
    "ImmutableConceptViolation",
    "OntologyGraphValidationError",
    "OntologyGraph",
    "OntologyRegistry",
    "SnapshotManager",
    "get_frozen_concepts",
]
