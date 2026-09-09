import osmnx as ox
import networkx as nx
from app.models.route import Coordinate
from app.utils.geo import haversine_distance
import logging

logger = logging.getLogger(__name__)


class MapService:
    def __init__(self):
        self._graph = None
        self._place_name = "Bali, Indonesia"

    def load_graph(self, place_name: str = None):
        if place_name:
            self._place_name = place_name

        logger.info(f"Loading map graph for {self._place_name}")
        try:
            self._graph = ox.graph_from_place(self._place_name, network_type="drive")
            self._graph = ox.add_edge_speeds(self._graph)
            self._graph = ox.add_edge_travel_times(self._graph)
            logger.info(f"Graph loaded: {len(self._graph.nodes)} nodes, {len(self._graph.edges)} edges")
        except Exception as e:
            logger.error(f"Error loading graph: {e}")
            self._graph = nx.DiGraph()

    def get_nearest_node(self, coord: Coordinate) -> int:
        if self._graph is None or len(self._graph.nodes) == 0:
            raise RuntimeError("Graph not loaded. Call load_graph() first.")
        return ox.distance.nearest_nodes(self._graph, coord.lng, coord.lat)

    def find_shortest_path(self, origin: Coordinate, destination: Coordinate) -> dict:
        if self._graph is None or len(self._graph.nodes) == 0:
            logger.warning("Graph not loaded, using fallback routing")
            return self._fallback_direct_route(origin, destination)

        orig_node = self.get_nearest_node(origin)
        dest_node = self.get_nearest_node(destination)

        try:
            path = nx.shortest_path(self._graph, orig_node, dest_node, weight="travel_time")
            edges = list(zip(path[:-1], path[1:]))

            total_distance = 0
            total_time = 0
            coordinates = []

            for u, v in edges:
                edge_data = self._graph.edges[u, v, 0]
                total_distance += edge_data.get("length", 0) / 1000
                total_time += edge_data.get("travel_time", 0) / 60

                node_data = self._graph.nodes[u]
                coordinates.append(Coordinate(lat=node_data["y"], lng=node_data["x"]))

            dest_node_data = self._graph.nodes[dest_node]
            coordinates.append(Coordinate(lat=dest_node_data["y"], lng=dest_node_data["x"]))

            return {
                "distance_km": round(total_distance, 2),
                "time_minutes": round(total_time, 2),
                "coordinates": coordinates,
                "path_nodes": path,
            }
        except nx.NetworkXNoPath:
            logger.warning(f"No path found from {origin} to {destination}")
            return self._fallback_direct_route(origin, destination)

    def find_alternative_paths(
        self, origin: Coordinate, destination: Coordinate, num_paths: int = 3
    ) -> list[dict]:
        if self._graph is None or len(self._graph.nodes) == 0:
            logger.warning("Graph not loaded, using fallback routing")
            return [self._fallback_direct_route(origin, destination)]

        orig_node = self.get_nearest_node(origin)
        dest_node = self.get_nearest_node(destination)
        paths = []

        try:
            for path in nx.shortest_simple_paths(self._graph, orig_node, dest_node, weight="travel_time"):
                if len(paths) >= num_paths:
                    break

                edges = list(zip(path[:-1], path[1:]))
                total_distance = 0
                total_time = 0
                coordinates = []

                for u, v in edges:
                    edge_data = self._graph.edges[u, v, 0]
                    total_distance += edge_data.get("length", 0) / 1000
                    total_time += edge_data.get("travel_time", 0) / 60
                    node_data = self._graph.nodes[u]
                    coordinates.append(Coordinate(lat=node_data["y"], lng=node_data["x"]))

                dest_node_data = self._graph.nodes[dest_node]
                coordinates.append(Coordinate(lat=dest_node_data["y"], lng=dest_node_data["x"]))

                paths.append({
                    "distance_km": round(total_distance, 2),
                    "time_minutes": round(total_time, 2),
                    "coordinates": coordinates,
                    "path_nodes": path,
                })
        except nx.NetworkXNoPath:
            paths.append(self._fallback_direct_route(origin, destination))

        return paths

    def _fallback_direct_route(self, origin: Coordinate, destination: Coordinate) -> dict:
        distance = haversine_distance(origin, destination)
        avg_speed_kmh = 40
        time_hours = distance / avg_speed_kmh

        coordinates = [
            Coordinate(lat=origin.lat, lng=origin.lng),
            Coordinate(
                lat=(origin.lat + destination.lat) / 2,
                lng=(origin.lng + destination.lng) / 2,
            ),
            Coordinate(lat=destination.lat, lng=destination.lng),
        ]

        return {
            "distance_km": round(distance, 2),
            "time_minutes": round(time_hours * 60, 2),
            "coordinates": coordinates,
            "path_nodes": [],
        }

    @property
    def is_loaded(self) -> bool:
        return self._graph is not None and len(self._graph.nodes) > 0


map_service = MapService()
