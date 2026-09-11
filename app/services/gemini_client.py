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


def generate_json(
    prompt: str,
    system: str,
    *,
    max_output_tokens: int = 64,
    timeout: float = 8.0,
) -> dict | None:
    """Panggil Gemini (keluarga Antigravity) dan ambil JSON dari teks respon.

    Mengembalikan dict hasil parse, atau None saat nonaktif/gagal agar aplikasi
    tetap berfungsi dengan fallback lokal.
    """
    settings = get_settings()
    model = settings.gemini_model
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": max_output_tokens,
            "responseMimeType": "application/json",
        },
    }
    try:
        resp = requests.post(
            _GENERATE_URL.format(model=model),
            json=body,
            headers={"x-goog-api-key": settings.gemini_api_key},
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
        if not text:
            return None
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001 - kegagalan harus degradasi tenang
        logger.warning("Gemini call gagal: %s", exc)
        return None
