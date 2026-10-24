"""
ParkFlow AI — Navigation Graph

Represents the 3-floor parking garage as a weighted directed graph.
Every slot is a node; edges represent drivable connections.
Floor transitions occur via ramps.

Graph Node Naming Convention:
  ENTRANCE               - Main vehicle entrance
  F1_ENTRY               - Floor 1 entry after entrance gate
  F1_JCT_A, F1_JCT_B    - Floor 1 intersections
  F1_RAMP_UP             - Ramp entry point (floor 1 → floor 2)
  F2_RAMP_DOWN           - Ramp exit (entering floor 2 from floor 1)
  F2_JCT_A, F2_JCT_B    - Floor 2 intersections
  F2_RAMP_UP             - Ramp entry point (floor 2 → floor 3)
  F3_RAMP_DOWN           - Ramp exit (entering floor 3)
  F3_JCT_A, F3_JCT_B    - Floor 3 intersections
  F1_A01 ... F3_C33      - Individual parking slot nodes
  EXIT                   - Garage exit
"""
import logging
import math
from typing import Dict, List, Optional, Tuple, Any
import networkx as nx

logger = logging.getLogger(__name__)

# Edge types for metadata
EDGE_STRAIGHT = "straight"
EDGE_TURN_LEFT = "turn_left"
EDGE_TURN_RIGHT = "turn_right"
EDGE_RAMP = "ramp"
EDGE_PARK = "park"


def _dist(meters: float) -> float:
    """Convert meters to graph weight (1:1 for simplicity)."""
    return meters


def build_garage_graph() -> nx.DiGraph:
    """
    Build the complete 3-floor parking garage navigation graph.
    Returns a directed weighted graph suitable for Dijkstra/A*.
    """
    G = nx.DiGraph()

    # ============================================================
    # NODE DEFINITIONS
    # ============================================================

    # ── Floor 1 Infrastructure ──────────────────────────────────
    f1_infra = {
        "ENTRANCE":    {"floor": 0, "label": "Entrance Gate",       "x": 50,  "y": 400, "node_type": "entrance"},
        "F1_ENTRY":    {"floor": 1, "label": "F1 Entry",            "x": 120, "y": 400, "node_type": "junction"},
        "F1_JCT_A":    {"floor": 1, "label": "F1 Junction A",       "x": 220, "y": 400, "node_type": "junction"},
        "F1_JCT_B":    {"floor": 1, "label": "F1 Junction B",       "x": 220, "y": 250, "node_type": "junction"},
        "F1_JCT_C":    {"floor": 1, "label": "F1 Junction C",       "x": 220, "y": 150, "node_type": "junction"},
        "F1_JCT_D":    {"floor": 1, "label": "F1 Junction D",       "x": 420, "y": 400, "node_type": "junction"},
        "F1_JCT_E":    {"floor": 1, "label": "F1 Junction E",       "x": 420, "y": 250, "node_type": "junction"},
        "F1_JCT_F":    {"floor": 1, "label": "F1 Junction F",       "x": 420, "y": 150, "node_type": "junction"},
        "F1_RAMP_UP":  {"floor": 1, "label": "F1 Ramp to Floor 2",  "x": 620, "y": 300, "node_type": "ramp"},
        "EXIT":        {"floor": 1, "label": "Exit",                 "x": 620, "y": 450, "node_type": "exit"},
    }

    # ── Floor 2 Infrastructure ──────────────────────────────────
    f2_infra = {
        "F2_RAMP_DOWN": {"floor": 2, "label": "F2 Ramp from F1",    "x": 620, "y": 300, "node_type": "ramp"},
        "F2_ENTRY":     {"floor": 2, "label": "F2 Entry",            "x": 520, "y": 300, "node_type": "junction"},
        "F2_JCT_A":     {"floor": 2, "label": "F2 Junction A",       "x": 420, "y": 400, "node_type": "junction"},
        "F2_JCT_B":     {"floor": 2, "label": "F2 Junction B",       "x": 420, "y": 250, "node_type": "junction"},
        "F2_JCT_C":     {"floor": 2, "label": "F2 Junction C",       "x": 420, "y": 150, "node_type": "junction"},
        "F2_JCT_D":     {"floor": 2, "label": "F2 Junction D",       "x": 220, "y": 400, "node_type": "junction"},
        "F2_JCT_E":     {"floor": 2, "label": "F2 Junction E",       "x": 220, "y": 250, "node_type": "junction"},
        "F2_JCT_F":     {"floor": 2, "label": "F2 Junction F",       "x": 220, "y": 150, "node_type": "junction"},
        "F2_RAMP_UP":   {"floor": 2, "label": "F2 Ramp to Floor 3",  "x": 120, "y": 300, "node_type": "ramp"},
    }

    # ── Floor 3 Infrastructure ──────────────────────────────────
    f3_infra = {
        "F3_RAMP_DOWN": {"floor": 3, "label": "F3 Ramp from F2",    "x": 120, "y": 300, "node_type": "ramp"},
        "F3_ENTRY":     {"floor": 3, "label": "F3 Entry",            "x": 220, "y": 300, "node_type": "junction"},
        "F3_JCT_A":     {"floor": 3, "label": "F3 Junction A",       "x": 220, "y": 400, "node_type": "junction"},
        "F3_JCT_B":     {"floor": 3, "label": "F3 Junction B",       "x": 220, "y": 250, "node_type": "junction"},
        "F3_JCT_C":     {"floor": 3, "label": "F3 Junction C",       "x": 220, "y": 150, "node_type": "junction"},
        "F3_JCT_D":     {"floor": 3, "label": "F3 Junction D",       "x": 420, "y": 400, "node_type": "junction"},
        "F3_JCT_E":     {"floor": 3, "label": "F3 Junction E",       "x": 420, "y": 250, "node_type": "junction"},
        "F3_JCT_F":     {"floor": 3, "label": "F3 Junction F",       "x": 420, "y": 150, "node_type": "junction"},
    }

    for node_id, attrs in {**f1_infra, **f2_infra, **f3_infra}.items():
        G.add_node(node_id, **attrs)

    # ============================================================
    # PARKING SLOT NODES (100 total)
    # Floor 1: F1-A01 to F1-A17 (row A), F1-B01 to F1-B17 (row B)
    # Floor 2: F2-B01 to F2-B17 (row B), F2-C01 to F2-C16 (row C)
    # Floor 3: F3-C01 to F3-C17, F3-D01 to F3-D16
    # ============================================================

    # Floor 1 slot layout: 2 rows of slots on each side of two aisles
    # Row A (17 slots) — left side of aisle 1
    # Row B (17 slots) — right side of aisle 2
    floor1_slots = []
    for i in range(1, 18):  # 17 slots in row A
        slot_id = f"F1-A{i:02d}"
        node_id = f"F1_A{i:02d}"
        x = 150 + (i - 1) * 28
        y = 100
        slot_type = "accessible" if i in (1, 2) else ("ev_charging" if i in (3, 4) else "standard")
        G.add_node(node_id, floor=1, label=slot_id, x=x, y=y, node_type="slot",
                   slot_code=slot_id, slot_type=slot_type)
        floor1_slots.append((node_id, slot_id))

    for i in range(1, 18):  # 17 slots in row B
        slot_id = f"F1-B{i:02d}"
        node_id = f"F1_B{i:02d}"
        x = 150 + (i - 1) * 28
        y = 450
        slot_type = "standard"
        G.add_node(node_id, floor=1, label=slot_id, x=x, y=y, node_type="slot",
                   slot_code=slot_id, slot_type=slot_type)
        floor1_slots.append((node_id, slot_id))

    # Floor 1: 34 slots total (need 34)  => A01-A17 (17) + B01-B17 (17) = 34 ✓

    # Floor 2 slots: B01-B17 (17) + C01-C16 (16) = 33
    floor2_slots = []
    for i in range(1, 18):
        slot_id = f"F2-B{i:02d}"
        node_id = f"F2_B{i:02d}"
        x = 320 + (i - 1) * 28  # Right half
        y = 100
        slot_type = "accessible" if i in (1, 2) else ("ev_charging" if i in (3, 4) else "standard")
        G.add_node(node_id, floor=2, label=slot_id, x=x, y=y, node_type="slot",
                   slot_code=slot_id, slot_type=slot_type)
        floor2_slots.append((node_id, slot_id))

    for i in range(1, 17):  # 16 slots
        slot_id = f"F2-C{i:02d}"
        node_id = f"F2_C{i:02d}"
        x = 320 + (i - 1) * 28
        y = 450
        slot_type = "standard"
        G.add_node(node_id, floor=2, label=slot_id, x=x, y=y, node_type="slot",
                   slot_code=slot_id, slot_type=slot_type)
        floor2_slots.append((node_id, slot_id))

    # Floor 3 slots: C01-C17 (17) + D01-D16 (16) = 33
    floor3_slots = []
    for i in range(1, 18):
        slot_id = f"F3-C{i:02d}"
        node_id = f"F3_C{i:02d}"
        x = 150 + (i - 1) * 28
        y = 100
        slot_type = "accessible" if i in (1, 2) else ("ev_charging" if i in (3, 4) else "standard")
        G.add_node(node_id, floor=3, label=slot_id, x=x, y=y, node_type="slot",
                   slot_code=slot_id, slot_type=slot_type)
        floor3_slots.append((node_id, slot_id))

    for i in range(1, 17):
        slot_id = f"F3-D{i:02d}"
        node_id = f"F3_D{i:02d}"
        x = 150 + (i - 1) * 28
        y = 450
        slot_type = "standard"
        G.add_node(node_id, floor=3, label=slot_id, x=x, y=y, node_type="slot",
                   slot_code=slot_id, slot_type=slot_type)
        floor3_slots.append((node_id, slot_id))

    # ============================================================
    # EDGES — FLOOR 1
    # ============================================================
    # Entrance → F1_ENTRY
    G.add_edge("ENTRANCE", "F1_ENTRY", weight=_dist(15), floor=1, edge_type=EDGE_STRAIGHT,
               direction="east", label="Enter garage")

    # F1 Main aisle backbone
    G.add_edge("F1_ENTRY", "F1_JCT_A", weight=_dist(20), floor=1, edge_type=EDGE_STRAIGHT,
               direction="east", label="Proceed to junction A")
    G.add_edge("F1_JCT_A", "F1_JCT_D", weight=_dist(30), floor=1, edge_type=EDGE_STRAIGHT,
               direction="east", label="Continue along main aisle")
    G.add_edge("F1_JCT_D", "F1_RAMP_UP", weight=_dist(25), floor=1, edge_type=EDGE_RAMP,
               direction="east", label="Proceed to ramp")
    G.add_edge("F1_JCT_D", "EXIT", weight=_dist(10), floor=1, edge_type=EDGE_STRAIGHT,
               direction="south", label="Head toward exit")

    # Cross-aisles floor 1
    G.add_edge("F1_JCT_A", "F1_JCT_B", weight=_dist(20), floor=1, edge_type=EDGE_TURN_LEFT,
               direction="north", label="Turn left, row B aisle")
    G.add_edge("F1_JCT_B", "F1_JCT_C", weight=_dist(20), floor=1, edge_type=EDGE_STRAIGHT,
               direction="north", label="Continue north")
    G.add_edge("F1_JCT_D", "F1_JCT_E", weight=_dist(20), floor=1, edge_type=EDGE_TURN_LEFT,
               direction="north", label="Turn left")
    G.add_edge("F1_JCT_E", "F1_JCT_F", weight=_dist(20), floor=1, edge_type=EDGE_STRAIGHT,
               direction="north", label="Continue north")

    # Connect left-side and right-side aisles
    G.add_edge("F1_JCT_B", "F1_JCT_E", weight=_dist(30), floor=1, edge_type=EDGE_STRAIGHT,
               direction="east", label="Cross aisle")
    G.add_edge("F1_JCT_C", "F1_JCT_F", weight=_dist(30), floor=1, edge_type=EDGE_STRAIGHT,
               direction="east", label="Cross aisle")

    # Slots Row A (top) — connected from aisle B level
    for i, (node_id, slot_id) in enumerate(floor1_slots[:17]):  # Row A
        # Slots connect to F1_JCT_B or F1_JCT_E depending on position
        jct = "F1_JCT_B" if i < 9 else "F1_JCT_E"
        w = _dist(5 + i * 2.5)
        G.add_edge(jct, node_id, weight=w, floor=1, edge_type=EDGE_PARK,
                   direction="north", label=f"Park at {slot_id}")
        G.add_edge(node_id, jct, weight=w, floor=1, edge_type=EDGE_STRAIGHT,
                   direction="south", label=f"Exit {slot_id}")

    # Slots Row B (bottom)
    for i, (node_id, slot_id) in enumerate(floor1_slots[17:]):  # Row B
        jct = "F1_JCT_A" if i < 9 else "F1_JCT_D"
        w = _dist(5 + i * 2.5)
        G.add_edge(jct, node_id, weight=w, floor=1, edge_type=EDGE_PARK,
                   direction="south", label=f"Park at {slot_id}")
        G.add_edge(node_id, jct, weight=w, floor=1, edge_type=EDGE_STRAIGHT,
                   direction="north", label=f"Exit {slot_id}")

    # ============================================================
    # RAMP — Floor 1 to Floor 2
    # ============================================================
    G.add_edge("F1_RAMP_UP", "F2_RAMP_DOWN", weight=_dist(40), floor=1,
               edge_type=EDGE_RAMP, direction="up", label="Take ramp to Floor 2")

    # ============================================================
    # EDGES — FLOOR 2
    # ============================================================
    G.add_edge("F2_RAMP_DOWN", "F2_ENTRY", weight=_dist(15), floor=2,
               edge_type=EDGE_STRAIGHT, direction="west", label="Enter Floor 2")
    G.add_edge("F2_ENTRY", "F2_JCT_A", weight=_dist(20), floor=2,
               edge_type=EDGE_STRAIGHT, direction="west", label="Head to junction A")
    G.add_edge("F2_JCT_A", "F2_JCT_D", weight=_dist(30), floor=2,
               edge_type=EDGE_STRAIGHT, direction="west", label="Continue along aisle")
    G.add_edge("F2_JCT_D", "F2_RAMP_UP", weight=_dist(25), floor=2,
               edge_type=EDGE_RAMP, direction="west", label="Proceed to ramp")

    G.add_edge("F2_JCT_A", "F2_JCT_B", weight=_dist(20), floor=2,
               edge_type=EDGE_TURN_LEFT, direction="north", label="Turn left")
    G.add_edge("F2_JCT_B", "F2_JCT_C", weight=_dist(20), floor=2,
               edge_type=EDGE_STRAIGHT, direction="north", label="Continue north")
    G.add_edge("F2_JCT_D", "F2_JCT_E", weight=_dist(20), floor=2,
               edge_type=EDGE_TURN_LEFT, direction="north", label="Turn left")
    G.add_edge("F2_JCT_E", "F2_JCT_F", weight=_dist(20), floor=2,
               edge_type=EDGE_STRAIGHT, direction="north", label="Continue north")
    G.add_edge("F2_JCT_B", "F2_JCT_E", weight=_dist(30), floor=2,
               edge_type=EDGE_STRAIGHT, direction="west", label="Cross aisle")
    G.add_edge("F2_JCT_C", "F2_JCT_F", weight=_dist(30), floor=2,
               edge_type=EDGE_STRAIGHT, direction="west", label="Cross aisle")
    G.add_edge("F2_ENTRY", "F2_JCT_B", weight=_dist(15), floor=2,
               edge_type=EDGE_TURN_LEFT, direction="north", label="Turn left")

    # F2 slots — Row B (top)
    for i, (node_id, slot_id) in enumerate(floor2_slots[:17]):
        jct = "F2_JCT_B" if i < 9 else "F2_JCT_E"
        w = _dist(5 + i * 2.5)
        G.add_edge(jct, node_id, weight=w, floor=2, edge_type=EDGE_PARK,
                   direction="north", label=f"Park at {slot_id}")
        G.add_edge(node_id, jct, weight=w, floor=2, edge_type=EDGE_STRAIGHT,
                   direction="south", label=f"Exit {slot_id}")

    # F2 slots — Row C (bottom)
    for i, (node_id, slot_id) in enumerate(floor2_slots[17:]):
        jct = "F2_JCT_A" if i < 8 else "F2_JCT_D"
        w = _dist(5 + i * 2.5)
        G.add_edge(jct, node_id, weight=w, floor=2, edge_type=EDGE_PARK,
                   direction="south", label=f"Park at {slot_id}")
        G.add_edge(node_id, jct, weight=w, floor=2, edge_type=EDGE_STRAIGHT,
                   direction="north", label=f"Exit {slot_id}")

    # ============================================================
    # RAMP — Floor 2 to Floor 3
    # ============================================================
    G.add_edge("F2_RAMP_UP", "F3_RAMP_DOWN", weight=_dist(40), floor=2,
               edge_type=EDGE_RAMP, direction="up", label="Take ramp to Floor 3")

    # ============================================================
    # EDGES — FLOOR 3
    # ============================================================
    G.add_edge("F3_RAMP_DOWN", "F3_ENTRY", weight=_dist(15), floor=3,
               edge_type=EDGE_STRAIGHT, direction="east", label="Enter Floor 3")
    G.add_edge("F3_ENTRY", "F3_JCT_A", weight=_dist(20), floor=3,
               edge_type=EDGE_STRAIGHT, direction="east", label="Head to junction A")
    G.add_edge("F3_JCT_A", "F3_JCT_D", weight=_dist(30), floor=3,
               edge_type=EDGE_STRAIGHT, direction="east", label="Continue along aisle")

    G.add_edge("F3_JCT_A", "F3_JCT_B", weight=_dist(20), floor=3,
               edge_type=EDGE_TURN_LEFT, direction="north", label="Turn left")
    G.add_edge("F3_JCT_B", "F3_JCT_C", weight=_dist(20), floor=3,
               edge_type=EDGE_STRAIGHT, direction="north", label="Continue north")
    G.add_edge("F3_JCT_D", "F3_JCT_E", weight=_dist(20), floor=3,
               edge_type=EDGE_TURN_LEFT, direction="north", label="Turn left")
    G.add_edge("F3_JCT_E", "F3_JCT_F", weight=_dist(20), floor=3,
               edge_type=EDGE_STRAIGHT, direction="north", label="Continue north")
    G.add_edge("F3_JCT_B", "F3_JCT_E", weight=_dist(30), floor=3,
               edge_type=EDGE_STRAIGHT, direction="east", label="Cross aisle")
    G.add_edge("F3_JCT_C", "F3_JCT_F", weight=_dist(30), floor=3,
               edge_type=EDGE_STRAIGHT, direction="east", label="Cross aisle")
    G.add_edge("F3_ENTRY", "F3_JCT_B", weight=_dist(15), floor=3,
               edge_type=EDGE_TURN_LEFT, direction="north", label="Turn left")

    # F3 slots — Row C (top)
    for i, (node_id, slot_id) in enumerate(floor3_slots[:17]):
        jct = "F3_JCT_B" if i < 9 else "F3_JCT_E"
        w = _dist(5 + i * 2.5)
        G.add_edge(jct, node_id, weight=w, floor=3, edge_type=EDGE_PARK,
                   direction="north", label=f"Park at {slot_id}")
        G.add_edge(node_id, jct, weight=w, floor=3, edge_type=EDGE_STRAIGHT,
                   direction="south", label=f"Exit {slot_id}")

    # F3 slots — Row D (bottom)
    for i, (node_id, slot_id) in enumerate(floor3_slots[17:]):
        jct = "F3_JCT_A" if i < 8 else "F3_JCT_D"
        w = _dist(5 + i * 2.5)
        G.add_edge(jct, node_id, weight=w, floor=3, edge_type=EDGE_PARK,
                   direction="south", label=f"Park at {slot_id}")
        G.add_edge(node_id, jct, weight=w, floor=3, edge_type=EDGE_STRAIGHT,
                   direction="north", label=f"Exit {slot_id}")

    logger.info(
        f"Navigation graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
    )
    return G


def get_slot_node(slot_code: str) -> str:
    """Convert a slot code like 'F2-B08' to its graph node ID 'F2_B08'."""
    return slot_code.replace("-", "_")


def get_all_slot_codes(G: nx.DiGraph) -> List[str]:
    """Return all slot codes defined in the graph."""
    return [
        G.nodes[n]["slot_code"]
        for n in G.nodes
        if G.nodes[n].get("node_type") == "slot"
    ]


# Singleton graph instance
_graph: Optional[nx.DiGraph] = None


def get_graph() -> nx.DiGraph:
    """Return the singleton garage navigation graph."""
    global _graph
    if _graph is None:
        _graph = build_garage_graph()
    return _graph


def reset_graph():
    """Force rebuild of the graph (used in tests)."""
    global _graph
    _graph = None
