"""
The graph, as plain data. No Dash, no Inngest, no OpenAI here - just the
shape of a workflow and the rules for it being valid, so this module can
be unit-tested on its own.

A node is either:
  - a "decision" node: has a prompt, and must have exactly one outgoing
    YES edge and one outgoing NO edge.
  - a "terminal" node: no prompt, no outgoing edges. Execution stops here.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

NodeType = Literal["decision", "terminal"]
Condition = Literal["YES", "NO"]


@dataclass
class Node:
    id: str
    label: str
    type: NodeType
    prompt: str | None = None


@dataclass
class Edge:
    source: str
    target: str
    condition: Condition


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    start_node: str | None = None

    # ---- mutation ----

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]
        if self.start_node == node_id:
            self.start_node = None

    def add_edge(self, edge: Edge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError("edge refers to a node that doesn't exist")
        if self.nodes[edge.source].type != "decision":
            raise ValueError(f"node '{edge.source}' is not a decision node, it can't have outgoing edges")
        # a decision node may have at most one YES and one NO edge
        existing = [e for e in self.edges if e.source == edge.source and e.condition == edge.condition]
        for e in existing:
            self.edges.remove(e)
        self.edges.append(edge)

    # ---- lookup ----

    def outgoing(self, node_id: str) -> dict[Condition, str]:
        return {e.condition: e.target for e in self.edges if e.source == node_id}

    def next_node(self, node_id: str, condition: Condition) -> str | None:
        return self.outgoing(node_id).get(condition)

    # ---- validation ----

    def validate(self) -> list[str]:
        """Returns a list of human-readable problems. Empty list = valid."""
        problems = []
        if not self.nodes:
            problems.append("graph has no nodes")
        if self.start_node is None:
            problems.append("no start node selected")
        elif self.start_node not in self.nodes:
            problems.append(f"start node '{self.start_node}' doesn't exist")

        for node in self.nodes.values():
            if node.type == "decision":
                if not node.prompt or not node.prompt.strip():
                    problems.append(f"decision node '{node.id}' has no prompt")
                out = self.outgoing(node.id)
                if "YES" not in out:
                    problems.append(f"decision node '{node.id}' has no YES edge")
                if "NO" not in out:
                    problems.append(f"decision node '{node.id}' has no NO edge")
            elif node.type == "terminal":
                if self.outgoing(node.id):
                    problems.append(f"terminal node '{node.id}' has outgoing edges (it shouldn't)")
        return problems

    # ---- (de)serialization ----

    def to_dict(self) -> dict:
        return {
            "nodes": {
                nid: {"id": n.id, "label": n.label, "type": n.type, "prompt": n.prompt}
                for nid, n in self.nodes.items()
            },
            "edges": [{"source": e.source, "target": e.target, "condition": e.condition} for e in self.edges],
            "start_node": self.start_node,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Graph":
        g = cls()
        for nid, n in data.get("nodes", {}).items():
            g.add_node(Node(id=n["id"], label=n["label"], type=n["type"], prompt=n.get("prompt")))
        for e in data.get("edges", []):
            g.edges.append(Edge(source=e["source"], target=e["target"], condition=e["condition"]))
        g.start_node = data.get("start_node")
        return g
