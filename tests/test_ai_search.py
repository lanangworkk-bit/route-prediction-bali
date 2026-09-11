from unittest.mock import MagicMock, patch

from app.config import Settings
from app.services.ai_search_service import search_parse


def test_search_disabled_without_key(monkeypatch):
    monkeypatch.setattr(
        "app.services.gemini_client.get_settings",
        lambda: Settings(gemini_api_key=""),
    )
    assert search_parse("cari tempat ngopi di Canggu") is None


def test_search_parses_mocked_response(monkeypatch):
    fake_settings = Settings(gemini_api_key="test-key", gemini_model="gemini-2.5-flash")
    monkeypatch.setattr("app.services.gemini_client.get_settings", lambda: fake_settings)
    monkeypatch.setattr("app.services.ai_search_service.is_enabled", lambda: True)

    mock_resp = MagicMock()
    payload = (
        '{"destination": "Pantai Kuta", "priority": "distance", '
        '"mode": "motorcycle", "note": "Rute santai di selatan Bali."}'
    )
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": payload}]}}]
    }
    with patch("requests.post", return_value=mock_resp):
        parsed = search_parse("bikin rute santai ke pantai yang tidak macet")

    assert parsed is not None
    assert parsed["destination"] == "Pantai Kuta"
    assert parsed["priority"] == "distance"
    assert parsed["mode"] == "motorcycle"
    assert parsed["note"]


def test_search_coerces_invalid_enum_values(monkeypatch):
    fake_settings = Settings(gemini_api_key="test-key", gemini_model="gemini-2.5-flash")
    monkeypatch.setattr("app.services.gemini_client.get_settings", lambda: fake_settings)
    monkeypatch.setattr("app.services.ai_search_service.is_enabled", lambda: True)

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{
            "text": '{"destination": "", "priority": "weird", "mode": "rocket", "note": "Halo."}'
        }]}}]
    }
    with patch("requests.post", return_value=mock_resp):
        parsed = search_parse("berapa lama ke Bedugul?")

    assert parsed["destination"] == ""
    assert parsed["priority"] == "time"
    assert parsed["mode"] == "car"
