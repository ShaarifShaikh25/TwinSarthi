"""
Causal Graph Definition for POLAR-TWIN Cascading Risk.
Transparent, deterministic, DAG-based representation of station dependencies.
"""
from typing import List, Dict, Set

# Node definitions
NODES = [
    "environment.temperature",
    "environment.wind",
    "energy.hvac",
    "energy.power",
    "infrastructure.generator",
    "fuel.reserve",
    "logistics.resupply",
    "mission.continuity"
]

# Directed edges representing causal relationships (source -> target)
EDGES = [
    ("environment.temperature", "energy.hvac"),
    ("environment.wind", "energy.hvac"),
    ("energy.hvac", "energy.power"),
    ("energy.power", "infrastructure.generator"),
    ("infrastructure.generator", "fuel.reserve"),
    ("fuel.reserve", "logistics.resupply"),
    ("logistics.resupply", "mission.continuity")
]

class CausalGraph:
    """Lightweight Python dictionary-based graph structure."""
    
    def __init__(self):
        self._forward: Dict[str, List[str]] = {node: [] for node in NODES}
        self._backward: Dict[str, List[str]] = {node: [] for node in NODES}
        
        for src, tgt in EDGES:
            if src in self._forward and tgt in self._forward:
                self._forward[src].append(tgt)
                self._backward[tgt].append(src)

    def get_dependencies(self, node: str) -> List[str]:
        """Returns immediate predecessors of a node."""
        return self._backward.get(node, [])

    def get_dependents(self, node: str) -> List[str]:
        """Returns immediate successors of a node."""
        return self._forward.get(node, [])

    def get_all_nodes(self) -> List[str]:
        """Returns topological ordering for cascading evaluation."""
        return NODES.copy()

def build_default_causal_graph() -> CausalGraph:
    """Factory method for the default POLAR-TWIN causal graph."""
    return CausalGraph()
