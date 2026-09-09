"""Bali coverage: all regencies/cities and popular destinations with coordinates."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BaliArea:
    name: str
    regency: str
    category: str
    lat: float
    lng: float


AREAS: list[BaliArea] = [
    # Kota Denpasar
    BaliArea("Denpasar", "Kota Denpasar", "Kota", -8.6525, 115.2193),
    BaliArea("Sanur", "Kota Denpasar", "Pantai", -8.6867, 115.2622),
    BaliArea("Renon", "Kota Denpasar", "Kota", -8.6765, 115.2340),
    # Kabupaten Badung
    BaliArea("Kuta", "Badung", "Pantai", -8.7234, 115.1723),
    BaliArea("Seminyak", "Badung", "Pantai", -8.6875, 115.1639),
    BaliArea("Canggu", "Badung", "Pantai", -8.6413, 115.1417),
    BaliArea("Jimbaran", "Badung", "Pantai", -8.7903, 115.1744),
    BaliArea("Uluwatu", "Badung", "Pura", -8.8291, 115.0849),
    BaliArea("Nusa Dua", "Badung", "Resort", -8.7934, 115.2280),
    BaliArea("Mengwi", "Badung", "Kabupaten", -8.5487, 115.1705),
    # Kabupaten Gianyar
    BaliArea("Ubud", "Gianyar", "Wisata", -8.5069, 115.2624),
    BaliArea("Gianyar", "Gianyar", "Kabupaten", -8.5411, 115.3189),
    BaliArea("Tegalalang", "Gianyar", "Sawah", -8.4334, 115.2812),
    # Kabupaten Bangli
    BaliArea("Bangli", "Bangli", "Kabupaten", -8.4542, 115.3597),
    BaliArea("Kintamani", "Bangli", "Gunung", -8.2537, 115.4010),
    # Kabupaten Klungkung
    BaliArea("Semarapura", "Klungkung", "Kabupaten", -8.5376, 115.4050),
    BaliArea("Nusa Penida", "Klungkung", "Pulau", -8.7241, 115.5456),
    # Kabupaten Karangasem
    BaliArea("Amlapura", "Karangasem", "Kabupaten", -8.4443, 115.6040),
    BaliArea("Amed", "Karangasem", "Pantai", -8.3387, 115.6320),
    BaliArea("Candi Dasa", "Karangasem", "Pantai", -8.5020, 115.5680),
    BaliArea("Tirta Gangga", "Karangasem", "Wisata", -8.4080, 115.5970),
    BaliArea("Tulamben", "Karangasem", "Laut", -8.2930, 115.5950),
    BaliArea("Padang Bai", "Karangasem", "Pelabuhan", -8.5240, 115.5110),
    # Kabupaten Buleleng
    BaliArea("Singaraja", "Buleleng", "Kabupaten", -8.1120, 115.0882),
    BaliArea("Lovina", "Buleleng", "Pantai", -8.1433, 115.0310),
    BaliArea("Munduk", "Buleleng", "Gunung", -8.2683, 115.0485),
    BaliArea("Pemuteran", "Buleleng", "Pantai", -8.1540, 114.6630),
    # Kabupaten Tabanan
    BaliArea("Tabanan", "Tabanan", "Kabupaten", -8.5402, 115.1200),
    BaliArea("Tanah Lot", "Tabanan", "Pura", -8.6214, 115.0867),
    BaliArea("Bedugul", "Tabanan", "Gunung", -8.2735, 115.1663),
    BaliArea("Jatiluwih", "Tabanan", "Sawah", -8.3590, 115.1280),
    # Kabupaten Jembrana
    BaliArea("Negara", "Jembrana", "Kabupaten", -8.3564, 114.6170),
    BaliArea("Gilimanuk", "Jembrana", "Pelabuhan", -8.1662, 114.4389),
]

REGENCIES: list[str] = [
    "Kota Denpasar",
    "Badung",
    "Gianyar",
    "Bangli",
    "Klungkung",
    "Karangasem",
    "Buleleng",
    "Tabanan",
    "Jembrana",
]


class AreaService:
    REGENCIES: list[str] = [
        "Kota Denpasar",
        "Badung",
        "Gianyar",
        "Bangli",
        "Klungkung",
        "Karangasem",
        "Buleleng",
        "Tabanan",
        "Jembrana",
    ]

    def list_areas(self) -> list[dict]:
        return [asdict(area) for area in AREAS]

    def search(self, query: str) -> list[dict]:
        q = query.strip().lower()
        if not q:
            return self.list_areas()
        return [
            asdict(area)
            for area in AREAS
            if q in area.name.lower() or q in area.regency.lower()
        ]

    def list_regencies(self) -> list[dict]:
        result = []
        for regency in self.REGENCIES:
            areas_in_regency = [a for a in AREAS if a.regency == regency]
            result.append({
                "name": regency,
                "areas": [
                    {"name": a.name, "lat": a.lat, "lng": a.lng}
                    for a in areas_in_regency
                ],
            })
        return result


area_service = AreaService()
