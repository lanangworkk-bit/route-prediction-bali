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


def _parse_json_text(text: str) -> dict | None:
    """Parse JSON yang bisa dibungkus markdown fence / teks tambahan."""
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    return json.loads(text[start : end + 1])


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
        parts = (payload.get("candidates") or [{}])[0].get("content", {}).get(
            "parts", []
        )
        for part in parts:
            text = (part.get("text") or "").strip()
            if not text:
                continue
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                parsed = _parse_json_text(text)
                if parsed is not None:
                    return parsed
        return None
    except Exception as exc:  # noqa: BLE001 - kegagalan harus degradasi tenang
        logger.warning("Gemini call gagal: %s", exc)
        return None
