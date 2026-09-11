import json
import logging

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

_GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def is_enabled() -> bool:
    return bool((get_settings().gemini_api_key or "").strip())


def refine_eta(context: dict, *, timeout: float = 8.0) -> tuple[float | None, str | None]:
    """Estimasi ETA dari Gemini (keluarga Antigravity) berbasis konteks rute.

    Mengembalikan (eta_minutes, provider_label). Bila API key kosong atau ada
    kegagalan jaringan, kembali (None, None) agar aplikasi tetap berfungsi
    dengan model lokal.
    """
    settings = get_settings()
    key = (settings.gemini_api_key or "").strip()
    if not key:
        return None, None
    model = settings.gemini_model

    prompt = (
        "Kamu penasihat estimasi waktu tempuh rute di Bali. Beberapa konteks "
        "(jarak, waktu dasar, lalu lintas, cuaca, insiden, jam, moda) ada di JSON "
        "berikut. Berikan satu perkiraan realistis untuk 'eta_minutes' dalam bentuk "
        "JSON ketat. Jangan menambah penjelasan apa pun.\n"
        + json.dumps(context, ensure_ascii=False)
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {
            "parts": [{"text": 'Return strict JSON: {"eta_minutes": number}'}]
        },
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 32,
            "responseMimeType": "application/json",
        },
    }

    try:
        resp = requests.post(
            _GENERATE_URL.format(model=model),
            json=body,
            headers={"x-goog-api-key": key},
            timeout=timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        text = (
            (payload.get("candidates") or [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )
        eta = float(json.loads(text).get("eta_minutes"))
    except Exception as exc:  # noqa: BLE001 - kegagalan harus degradasi tenang
        logger.warning("Gemini ETA refinement gagal: %s", exc)
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
