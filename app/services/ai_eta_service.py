import logging

from app.config import get_settings
from app.services.gemini_client import generate_json, is_enabled

logger = logging.getLogger(__name__)


def refine_eta(context: dict, *, timeout: float = 8.0) -> tuple[float | None, str | None]:
    """Estimasi ETA dari Gemini (keluarga Antigravity) berbasis konteks rute.

    Mengembalikan (eta_minutes, provider_label). Bila API key kosong atau ada
    kegagalan jaringan, kembali (None, None) agar aplikasi tetap berfungsi
    dengan model lokal.
    """
    settings = get_settings()
    if not is_enabled():
        return None, None
    model = settings.gemini_model

    prompt = (
        "Kamu penasihat estimasi waktu tempuh rute di Bali. Beberapa konteks "
        "(jarak, waktu dasar, lalu lintas, cuaca, insiden, jam, moda) ada di JSON "
        "berikut. Berikan satu perkiraan realistis untuk 'eta_minutes' dalam bentuk "
        "JSON ketat. Jangan menambah penjelasan apa pun.\n"
        + str(context)
    )

    data = generate_json(
        prompt,
        'Return strict JSON: {"eta_minutes": number}',
        max_output_tokens=32,
        timeout=timeout,
    )
    if data is None:
        return None, None
    try:
        eta = float(data.get("eta_minutes"))
    except (TypeError, ValueError):
        return None, None
    if not (0 < eta < 3000):
        return None, None
    return round(eta, 2), f"gemini:{model}"


def blend(
    eta_minutes: float, gemini_minutes: float | None, weight: float | None = None
) -> tuple[float, dict]:
    """Campur ETA heuristik/ML dengan estimasi Gemini, diklamp agar wajar."""
    if gemini_minutes is None or gemini_minutes <= 0:
        return eta_minutes, {}
    settings = get_settings()
    w = settings.gemini_eta_weight if weight is None else weight
    lo, hi = eta_minutes * 0.6, eta_minutes * 1.8
    g = min(max(gemini_minutes, lo), hi)
    blended = eta_minutes * (1 - w) + g * w
    return blended, {
        "provider": "antigravity",
        "model": settings.gemini_model,
        "gemini_predicted_minutes": round(g, 2),
        "gemini_weight": w,
    }
