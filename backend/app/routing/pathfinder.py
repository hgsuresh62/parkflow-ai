"""
ParkFlow AI — AI Pathfinding Engine

Implements Dijkstra's shortest-path algorithm on the garage navigation graph.
Generates human-readable turn-by-turn navigation instructions.
Supports dynamic route recalculation when slots become unavailable.
"""
import logging
import math
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import networkx as nx

from app.routing.graph import get_graph, get_slot_node, EDGE_RAMP, EDGE_PARK

logger = logging.getLogger(__name__)

# Average driving speed in parking garage (m/s)
GARAGE_SPEED_MPS = 2.5  # ~9 km/h


@dataclass
class NavigationInstruction:
    step: int
    instruction: str
    floor: int
    node_from: str
    node_to: str
    edge_type: str
    direction: str
    distance_m: float


@dataclass
class RouteResult:
    destination_slot: str
    source_node: str
    destination_node: str
    path: List[str]
    instructions: List[Dict[str, Any]]
    distance_m: float
    estimated_time_seconds: int
    route_cost: float
    floor_changes: List[Dict[str, Any]]
    is_feasible: bool
    error: Optional[str] = None


class PathfindingEngine:
    """
    Dijkstra-based pathfinding for the 3-floor parking garage.
    """

    def __init__(self):
        self.graph = get_graph()

    def find_route(
        self,
        source_node: str,
        destination_slot_code: str,
        blocked_slots: Optional[List[str]] = None,
    ) -> RouteResult:
        """
        Calculate the optimal route from source_node to a parking slot.

        Args:
            source_node: Starting graph node (e.g., "ENTRANCE")
            destination_slot_code: Target slot code (e.g., "F2-B08")
            blocked_slots: Optional list of slot codes to treat as unavailable

        Returns:
            RouteResult with path, instructions, and metadata
        """
        destination_node = get_slot_node(destination_slot_code)
        blocked_slots = blocked_slots or []

        # Validate source exists
        if source_node not in self.graph:
            return RouteResult(
                destination_slot=destination_slot_code,
                source_node=source_node,
                destination_node=destination_node,
                path=[],
                instructions=[],
                distance_m=0,
                estimated_time_seconds=0,
                route_cost=0,
                floor_changes=[],
                is_feasible=False,
                error=f"Source node '{source_node}' not found in navigation graph",
            )

        # Validate destination exists
        if destination_node not in self.graph:
            return RouteResult(
                destination_slot=destination_slot_code,
                source_node=source_node,
                destination_node=destination_node,
                path=[],
                instructions=[],
                distance_m=0,
                estimated_time_seconds=0,
                route_cost=0,
                floor_changes=[],
                is_feasible=False,
                error=f"Destination slot '{destination_slot_code}' not found in navigation graph",
            )

        # Build a filtered view excluding blocked slots
        working_graph = self._build_filtered_graph(blocked_slots, destination_node)

        # Run Dijkstra's algorithm
        try:
            path = nx.dijkstra_path(working_graph, source_node, destination_node, weight="weight")
            cost = nx.dijkstra_path_length(working_graph, source_node, destination_node, weight="weight")
        except nx.NetworkXNoPath:
            return RouteResult(
                destination_slot=destination_slot_code,
                source_node=source_node,
                destination_node=destination_node,
                path=[],
                instructions=[],
                distance_m=0,
                estimated_time_seconds=0,
                route_cost=0,
                floor_changes=[],
                is_feasible=False,
                error=f"No feasible route found to '{destination_slot_code}'. The destination may be blocked or unreachable.",
            )
        except nx.NodeNotFound as e:
            return RouteResult(
                destination_slot=destination_slot_code,
                source_node=source_node,
                destination_node=destination_node,
                path=[],
                instructions=[],
                distance_m=0,
                estimated_time_seconds=0,
                route_cost=0,
                floor_changes=[],
                is_feasible=False,
                error=str(e),
            )

        # Calculate actual distance and time
        distance_m = self._calculate_path_distance(path)
        estimated_time = int(distance_m / GARAGE_SPEED_MPS)

        # Identify floor changes
        floor_changes = self._identify_floor_changes(path)

        # Generate turn-by-turn instructions
        instructions = self._generate_instructions(path)

        return RouteResult(
            destination_slot=destination_slot_code,
            source_node=source_node,
            destination_node=destination_node,
            path=path,
            instructions=instructions,
            distance_m=round(distance_m, 1),
            estimated_time_seconds=estimated_time,
            route_cost=round(cost, 2),
            floor_changes=floor_changes,
            is_feasible=True,
        )

    def find_alternative_slots(
        self,
        source_node: str,
        preferred_floor: Optional[int] = None,
        count: int = 5,
        available_slot_codes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find the nearest available slots, ranked by route cost.
        """
        if not available_slot_codes:
            return []

        alternatives = []
        for slot_code in available_slot_codes:
            result = self.find_route(source_node, slot_code)
            if result.is_feasible:
                node = get_slot_node(slot_code)
                node_data = self.graph.nodes.get(node, {})
                slot_floor = node_data.get("floor", 0)
                # Small penalty for non-preferred floors
                floor_penalty = 0 if preferred_floor is None else (5 * abs(slot_floor - preferred_floor))
                alternatives.append({
                    "slot_code": slot_code,
                    "floor": slot_floor,
                    "distance_m": result.distance_m,
                    "estimated_time_seconds": result.estimated_time_seconds,
                    "route_cost": result.route_cost + floor_penalty,
                })

        alternatives.sort(key=lambda x: x["route_cost"])
        return alternatives[:count]

    def _build_filtered_graph(
        self, blocked_slots: List[str], destination_node: str
    ) -> nx.DiGraph:
        """
        Build a copy of the graph with blocked slots removed
        (except the destination itself).
        """
        if not blocked_slots:
            return self.graph

        blocked_nodes = [
            get_slot_node(s) for s in blocked_slots
            if get_slot_node(s) != destination_node
        ]

        if not blocked_nodes:
            return self.graph

        filtered = self.graph.copy()
        for node in blocked_nodes:
            if node in filtered:
                filtered.remove_node(node)
        return filtered

    def _calculate_path_distance(self, path: List[str]) -> float:
        """Sum edge weights along the path."""
        total = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.graph.get_edge_data(u, v, default={})
            total += edge_data.get("weight", 10.0)
        return total

    def _identify_floor_changes(self, path: List[str]) -> List[Dict[str, Any]]:
        """Detect ramp transitions in the path."""
        changes = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self.graph.get_edge_data(u, v, default={})
            if edge.get("edge_type") == EDGE_RAMP:
                from_floor = self.graph.nodes[u].get("floor", 0)
                to_floor = self.graph.nodes[v].get("floor", 0)
                if from_floor != to_floor:
                    changes.append({
                        "step_index": i,
                        "from_node": u,
                        "to_node": v,
                        "from_floor": from_floor,
                        "to_floor": to_floor,
                        "direction": "up" if to_floor > from_floor else "down",
                    })
        return changes

    def _generate_instructions(self, path: List[str]) -> List[Dict[str, Any]]:
        """
        Generate human-readable turn-by-turn navigation instructions
        from an ordered path of graph nodes.
        """
        instructions = []
        step = 1

        # Group consecutive same-direction, same-floor segments
        i = 0
        while i < len(path) - 1:
            u = path[i]
            v = path[i + 1]
            edge = self.graph.get_edge_data(u, v, default={})
            edge_type = edge.get("edge_type", "straight")
            edge_label = edge.get("label", "")
            floor_num = self.graph.nodes[u].get("floor", 1)
            direction = edge.get("direction", "")

            u_label = self.graph.nodes[u].get("label", u)
            v_label = self.graph.nodes[v].get("label", v)
            v_type = self.graph.nodes[v].get("node_type", "junction")

            if edge_type == EDGE_RAMP:
                from_floor = self.graph.nodes[u].get("floor", 1)
                to_floor = self.graph.nodes[v].get("floor", 1)
                if to_floor > from_floor:
                    instr = f"Take the ramp up to Floor {to_floor}."
                else:
                    instr = f"Take the ramp down to Floor {to_floor}."
                instructions.append({
                    "step": step,
                    "instruction": instr,
                    "floor": from_floor,
                    "floor_change": True,
                    "to_floor": to_floor,
                    "node_from": u,
                    "node_to": v,
                    "edge_type": edge_type,
                })
            elif edge_type == EDGE_PARK:
                slot_label = v_label
                instructions.append({
                    "step": step,
                    "instruction": f"Park in slot {slot_label}. You have arrived at your destination.",
                    "floor": floor_num,
                    "floor_change": False,
                    "node_from": u,
                    "node_to": v,
                    "edge_type": edge_type,
                })
            else:
                # Determine turn direction from edge type
                if edge_type == "turn_left":
                    turn = "Turn left"
                elif edge_type == "turn_right":
                    turn = "Turn right"
                else:
                    turn = "Continue straight"

                if v_type == "junction":
                    instr = f"{turn} and proceed to {v_label} on Floor {floor_num}."
                elif v_type == "ramp":
                    instr = f"{turn} and follow the signs toward the ramp on Floor {floor_num}."
                elif v_type == "exit":
                    instr = f"Proceed to the exit."
                else:
                    instr = f"{turn} — {edge_label}"

                instructions.append({
                    "step": step,
                    "instruction": instr,
                    "floor": floor_num,
                    "floor_change": False,
                    "node_from": u,
                    "node_to": v,
                    "edge_type": edge_type,
                })

            step += 1
            i += 1

        return instructions


# Module-level singleton
_engine: Optional[PathfindingEngine] = None


def get_pathfinding_engine() -> PathfindingEngine:
    """Return the singleton pathfinding engine."""
    global _engine
    if _engine is None:
        _engine = PathfindingEngine()
    return _engine
