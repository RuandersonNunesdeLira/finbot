"""
WAHA (WhatsApp HTTP API) integration service.
"""
import httpx
from loguru import logger
from backend.config import get_settings


class WAHAService:
    """Integration with WAHA for WhatsApp messaging."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.waha_api_url
        self._session = settings.waha_session_name
        self._api_key = settings.waha_api_key
        self._webhook_url = "http://backend:8080/api/waha/webhook"
        logger.info(f"WAHA Service initialized: {self._base_url}, session: {self._session}")

    @property
    def _headers(self) -> dict:
        """Common headers with API Key authentication."""
        return {"X-Api-Key": self._api_key}

    @property
    def _session_config(self) -> dict:
        """Session configuration with webhook."""
        return {
            "name": self._session,
            "config": {
                "webhooks": [
                    {
                        "url": self._webhook_url,
                        "events": ["message", "session.status"],
                    }
                ]
            },
        }



    async def create_and_start_session(self) -> dict:
        """
        Ensure session exists with correct webhook config, then start it.
        - If session doesn't exist:  POST /api/sessions  (creates + starts)
        - If session already exists: PUT /api/sessions/{session} (updates webhook config)
        - Then start:                POST /api/sessions/{session}/start (idempotent)
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Step 1 — Check if session exists
                check = await client.get(
                    f"{self._base_url}/api/sessions/{self._session}",
                    headers=self._headers,
                )

                if check.status_code == 200:
                    # Session exists — update it with webhook config
                    logger.info("WAHA session exists, updating webhook config...")
                    resp = await client.put(
                        f"{self._base_url}/api/sessions/{self._session}",
                        json=self._session_config,
                        headers=self._headers,
                    )
                    if resp.status_code == 200:
                        logger.info(f"WAHA session updated with webhook: {self._webhook_url}")
                    else:
                        logger.warning(f"WAHA update session: {resp.status_code} {resp.text}")
                else:
                    # Session doesn't exist — create it
                    logger.info("WAHA session not found, creating...")
                    resp = await client.post(
                        f"{self._base_url}/api/sessions",
                        json=self._session_config,
                        headers=self._headers,
                    )
                    if resp.status_code in (200, 201):
                        logger.info(f"WAHA session created with webhook: {self._webhook_url}")
                    else:
                        logger.warning(f"WAHA create session: {resp.status_code} {resp.text}")

                # Step 2 — Start session (idempotent)
                resp = await client.post(
                    f"{self._base_url}/api/sessions/{self._session}/start",
                    headers=self._headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info(f"WAHA session started: status={data.get('status')}")
                    return data
                else:
                    logger.warning(f"WAHA start session: {resp.status_code} {resp.text}")
                    return {"status": "error", "detail": resp.text}

        except Exception as e:
            logger.error(f"WAHA session init error: {e}")
            return {"status": "error", "detail": str(e)}

    async def get_qr_code(self) -> dict:
        """
        Get the QR code for WhatsApp authentication.
        Endpoint: GET /api/{session}/auth/qr

        Tries base64 JSON first (Accept: application/json),
        then falls back to raw format.
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Try base64 JSON format
                resp = await client.get(
                    f"{self._base_url}/api/{self._session}/auth/qr",
                    headers={**self._headers, "Accept": "application/json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Returns {"mimetype": "image/png", "data": "base64..."}
                    if data.get("data"):
                        return {"qr": data["data"], "status": "scan_qr", "format": "image"}

                # Fallback: raw format
                resp = await client.get(
                    f"{self._base_url}/api/{self._session}/auth/qr",
                    params={"format": "raw"},
                    headers={**self._headers, "Accept": "application/json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Returns {"value": "qr-code-raw-data"}
                    if data.get("value"):
                        return {"qr": data["value"], "status": "scan_qr", "format": "raw"}

                logger.warning(f"QR code not available: HTTP {resp.status_code}")
                return {"qr": None, "status": "unavailable", "detail": f"HTTP {resp.status_code}"}
        except Exception as e:
            logger.error(f"WAHA QR code error: {e}")
            return {"qr": None, "status": "error", "detail": str(e)}

    async def get_status(self) -> dict:
        """
        Get the current session status.
        Endpoint: GET /api/sessions/{session}
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self._base_url}/api/sessions/{self._session}",
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "connected": data.get("status") == "WORKING",
                    "status": data.get("status", "unknown"),
                    "session_name": self._session,
                }
        except Exception as e:
            logger.warning(f"WAHA status check failed: {e}")
            return {
                "connected": False,
                "status": "disconnected",
                "session_name": self._session,
            }

    async def send_message(self, chat_id: str, text: str) -> dict:
        """
        Send a text message via WhatsApp.
        Endpoint: POST /api/sendText
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self._base_url}/api/sendText",
                    json={
                        "session": self._session,
                        "chatId": chat_id,
                        "text": text,
                    },
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"Message sent to {chat_id[:15]}...")
                return data
        except Exception as e:
            logger.error(f"WAHA send message error: {e}")
            return {"error": str(e)}


# Singleton
_waha_service: WAHAService | None = None


def get_waha_service() -> WAHAService:
    """Get or create the WAHAService singleton."""
    global _waha_service
    if _waha_service is None:
        _waha_service = WAHAService()
    return _waha_service
