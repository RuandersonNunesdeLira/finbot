
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path




class TestToolsService:


    def test_resolve_coin_id_known(self):
        from backend.services.tools_service import _resolve_coin_id
        assert _resolve_coin_id("btc") == "bitcoin"
        assert _resolve_coin_id("Bitcoin") == "bitcoin"
        assert _resolve_coin_id("ETH") == "ethereum"
        assert _resolve_coin_id("sol") == "solana"

    def test_resolve_coin_id_unknown(self):
        from backend.services.tools_service import _resolve_coin_id
        assert _resolve_coin_id("unknowncoin") == "unknowncoin"

    @patch("backend.services.tools_service.httpx.get")
    def test_get_crypto_price_success(self, mock_get):
        from backend.services.tools_service import get_crypto_price

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "bitcoin": {
                "usd": 65000.50,
                "usd_24h_change": 2.5,
                "usd_market_cap": 1250000000000,
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_crypto_price.invoke({"coin_name": "btc", "currency": "usd"})
        assert "65,000.50" in result
        assert "+2.50%" in result
        assert "BTC" in result.upper()

    @patch("backend.services.tools_service.httpx.get")
    def test_get_crypto_price_not_found(self, mock_get):
        from backend.services.tools_service import get_crypto_price

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_crypto_price.invoke({"coin_name": "fakecoin123"})
        assert "not found" in result.lower()

    @patch("backend.services.tools_service.httpx.get")
    def test_get_trending_crypto_success(self, mock_get):
        from backend.services.tools_service import get_trending_crypto

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "coins": [
                {"item": {"name": "Bitcoin", "symbol": "BTC", "market_cap_rank": 1, "price_btc": 1.0}},
                {"item": {"name": "Ethereum", "symbol": "ETH", "market_cap_rank": 2, "price_btc": 0.05}},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_trending_crypto.invoke({})
        assert "Bitcoin" in result
        assert "Ethereum" in result
        assert "Trending" in result




class TestFeedbackService:


    def setup_method(self):
        """Reset the singleton before each test."""
        import backend.services.feedback_service as fb_mod
        fb_mod._feedback_service = None
        # Use temp paths
        fb_mod.FEEDBACK_FILE = Path("/tmp/test_feedbacks.json")
        fb_mod.PROMPT_FILE = Path("/tmp/test_prompts.json")
        # Clean up
        fb_mod.FEEDBACK_FILE.unlink(missing_ok=True)
        fb_mod.PROMPT_FILE.unlink(missing_ok=True)

    def test_initial_prompt_exists(self):
        from backend.services.feedback_service import get_feedback_service
        svc = get_feedback_service()
        assert svc.get_current_version() == 1
        assert "FinBot" in svc.get_current_prompt()

    def test_add_feedback(self):
        from backend.services.feedback_service import get_feedback_service
        svc = get_feedback_service()
        entry = svc.add_feedback(rating=4, comment="Good response", suggestion="Be more concise")
        assert entry.rating == 4
        assert entry.comment == "Good response"
        assert len(svc.get_feedbacks()) == 1

    def test_update_prompt(self):
        from backend.services.feedback_service import get_feedback_service
        svc = get_feedback_service()
        new_version = svc.update_prompt("New improved prompt", "Test update")
        assert new_version.version == 2
        assert svc.get_current_prompt() == "New improved prompt"
        assert len(svc.get_prompt_history()) == 2

    def test_unapplied_feedbacks(self):
        from backend.services.feedback_service import get_feedback_service
        svc = get_feedback_service()
        svc.add_feedback(rating=2, comment="Bad", suggestion="Fix it")
        svc.add_feedback(rating=3, comment="OK", suggestion="")
        assert len(svc.get_unapplied_feedbacks()) == 2

        svc.update_prompt("Better prompt", "Applied feedback")
        assert len(svc.get_unapplied_feedbacks()) == 0

    def test_persistence(self):
        """Test that data survives service recreation."""
        import backend.services.feedback_service as fb_mod

        svc = fb_mod.get_feedback_service()
        svc.add_feedback(rating=5, comment="Excellent!", suggestion="")
        svc.update_prompt("Persisted prompt", "Persistence test")

        # Reset singleton to force reload from disk
        fb_mod._feedback_service = None
        svc2 = fb_mod.get_feedback_service()

        assert svc2.get_current_version() == 2
        assert svc2.get_current_prompt() == "Persisted prompt"
        assert len(svc2.get_feedbacks()) == 1




class TestSchemas:


    def test_chat_request_valid(self):
        from backend.models.schemas import ChatRequest
        req = ChatRequest(message="Hello")
        assert req.message == "Hello"
        assert req.session_id == "streamlit"

    def test_chat_request_empty_message(self):
        from backend.models.schemas import ChatRequest
        with pytest.raises(Exception):
            ChatRequest(message="")

    def test_feedback_request_valid(self):
        from backend.models.schemas import FeedbackRequest
        req = FeedbackRequest(rating=4, comment="Good", suggestion="Be brief")
        assert req.rating == 4

    def test_feedback_request_rating_bounds(self):
        from backend.models.schemas import FeedbackRequest
        with pytest.raises(Exception):
            FeedbackRequest(rating=0)
        with pytest.raises(Exception):
            FeedbackRequest(rating=6)
