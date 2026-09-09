import folium

from app.config import get_settings
from app.models.route import RouteInfo, RouteResponse
from app.services.traffic_service import traffic_service

TRAFFIC_COLORS = {
    "lancar": "#2E8B57",
    "normal": "#A9A727",
    "padat": "#E67E22",
    "macet": "#C0392B",
}


class VisualizationService:
    def __init__(self):
        self.settings = get_settings()

    def create_route_map(self, response: RouteResponse) -> folium.Map:
        best = response.best_route
        first = best.coordinates[0]
        last = best.coordinates[-1]
        center_lat = (first.lat + last.lat) / 2
        center_lng = (first.lng + last.lng) / 2

        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=13,
            tiles="OpenStreetMap",
        )

        self._add_route(m, response.alternative_routes, is_best=False)
        self._add_traffic_segments(m, best)
        self._add_route(m, [response.best_route], is_best=True)

        self._add_markers(m, response)

        self._add_info_panel(m, response)

        return m

    def _add_traffic_segments(self, map_obj: folium.Map, route: RouteInfo):
        segments = traffic_service.get_segment_traffic(route.coordinates, segments=6)
        for seg in segments:
            folium.PolyLine(
                locations=[
                    [seg["start"]["lat"], seg["start"]["lng"]],
                    [seg["end"]["lat"], seg["end"]["lng"]],
                ],
                weight=9,
                color=TRAFFIC_COLORS[seg["level"]],
                opacity=0.45,
                popup=f"Lalu lintas: {seg['level']} ({seg['congestion']:.0%})",
            ).add_to(map_obj)

    def _add_route(self, map_obj: folium.Map, routes: list[RouteInfo], is_best: bool):
        color = "#2E8B57" if is_best else "#808080"
        weight = 6 if is_best else 3
        opacity = 1.0 if is_best else 0.6
        label = "Rute Terbaik" if is_best else "Rute Alternatif"

        for i, route in enumerate(routes):
            coordinates = [(c.lat, c.lng) for c in route.coordinates]

            if len(coordinates) > 2:
                folium.PolyLine(
                    coordinates,
                    weight=weight,
                    color=color,
                    opacity=opacity,
                    popup=folium.Popup(
                        f"""
                        <b>{label} {i + 1}</b><br>
                        Jarak: {route.distance_km} km<br>
                        Estimasi: {route.estimated_time_minutes} menit<br>
                        Skor: {route.overall_score}/100<br>
                        Kondisi: {route.road_conditions.get('traffic_level', 'N/A')}
                        """,
                        max_width=250,
                    ),
                ).add_to(map_obj)

    def _add_markers(self, map_obj: folium.Map, response: RouteResponse):
        origin = response.best_route.coordinates[0]
        destination = response.best_route.coordinates[-1]

        folium.Marker(
            [origin.lat, origin.lng],
            popup="<b>Titik Awal</b>",
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
        ).add_to(map_obj)

        for i, waypoint in enumerate(response.waypoints, start=1):
            folium.Marker(
                [waypoint.lat, waypoint.lng],
                popup=f"<b>Titik Singgah {i}</b>",
                icon=folium.Icon(color="orange", icon="map-marker", prefix="fa"),
            ).add_to(map_obj)

        folium.Marker(
            [destination.lat, destination.lng],
            popup="<b>Tujuan</b>",
            icon=folium.Icon(color="red", icon="flag", prefix="fa"),
        ).add_to(map_obj)

    def _add_info_panel(self, map_obj: folium.Map, response: RouteResponse):
        best = response.best_route
        weather = response.weather_summary

        info_html = f"""
        <div style="
            position: fixed;
            bottom: 30px;
            left: 30px;
            z-index: 1000;
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif;
            max-width: 300px;
        ">
            <h4 style="margin: 0 0 10px 0; color: #2E8B57;">Prediksi Rute Terbaik</h4>
            <p style="margin: 5px 0;"><b>Jarak:</b> {best.distance_km} km</p>
            <p style="margin: 5px 0;"><b>Estimasi:</b> {best.estimated_time_minutes} menit</p>
            <p style="margin: 5px 0;"><b>Skor:</b> {best.overall_score}/100</p>
            <p style="margin: 5px 0;"><b>Lalu Lintas:</b> {best.road_conditions.get('traffic_level', 'N/A')}</p>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0;"><b>Legenda Lalu Lintas:</b></p>
            <p style="margin: 3px 0;"><span style="color:#2E8B57;">━</span> Lancar &nbsp;
            <span style="color:#A9A727;">━</span> Normal &nbsp;
            <span style="color:#E67E22;">━</span> Padat &nbsp;
            <span style="color:#C0392B;">━</span> Macet</p>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0;"><b>Cuaca:</b> {weather.get('condition', 'N/A')}</p>
            <p style="margin: 5px 0;"><b>Suhu:</b> {weather.get('temperature', 'N/A')}°C</p>
            <p style="margin: 5px 0;"><b>Saran:</b> {weather.get('impact', 'N/A')}</p>
        </div>
        """

        map_obj.get_root().html.add_child(folium.Element(info_html))

    def save_map(self, map_obj: folium.Map, filename: str = "route_map.html"):
        map_obj.save(filename)
        return filename


visualization_service = VisualizationService()
