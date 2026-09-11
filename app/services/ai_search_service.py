import logging

from app.services.gemini_client import generate_json, is_enabled

logger = logging.getLogger(__name__)

_SEARCH_SYSTEM = (
    "Kamu asisten navigasi Bahasa Indonesia untuk aplikasi rute di Bali. "
    'Terjemahkan permintaan pengguna ke JSON ketat dengan field: '
    '"destination" (nama tempat/daerah yang jelas, mis. "Pantai Kuta" atau "Bedugul"), '
    '"priority" (salah satu: "time" | "distance" | "relaxed"), '
    '"mode" (salah satu: "car" | "motorcycle" | "walking"), '
    'dan "note" (jawaban ringkas 1 kalimat dalam Bahasa Indonesia ke pengemudi, '
    'boleh berisi alasan/scenic route). Jika pengguna hanya bertanya tanpa tujuan, '
    'isi "destination" dengan string kosong dan jawab lewat "note".'
)


def search_parse(query: str, *, timeout: float = 10.0) -> dict | None:
    """Parse bahasa alami menjadi (tujuan, preferensi, jawaban). None bila nonaktif/gagal."""
    if not is_enabled():
        return None
    prompt = "Permintaan pengguna:\n" + (query or "").strip()
    data = generate_json(prompt, _SEARCH_SYSTEM, max_output_tokens=120, timeout=timeout)
    if not data:
        return None
    priority = data.get("priority")
    if priority not in ("time", "distance", "relaxed"):
        priority = "time"
    mode = data.get("mode")
    if mode not in ("car", "motorcycle", "walking"):
        mode = "car"
    return {
        "destination": str(data.get("destination") or "").strip(),
        "priority": priority,
        "mode": mode,
        "note": str(data.get("note") or "").strip(),
    }
