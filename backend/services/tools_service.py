"""
CoinGecko tools for crypto price and trend lookups.
"""
import httpx
from langchain_core.tools import tool
from loguru import logger

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


COIN_ALIASES: dict[str, str] = {
    "bitcoin": "bitcoin", "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "solana": "solana", "sol": "solana",
    "cardano": "cardano", "ada": "cardano",
    "dogecoin": "dogecoin", "doge": "dogecoin",
    "ripple": "ripple", "xrp": "ripple",
    "polkadot": "polkadot", "dot": "polkadot",
    "avalanche": "avalanche-2", "avax": "avalanche-2",
    "chainlink": "chainlink", "link": "chainlink",
    "litecoin": "litecoin", "ltc": "litecoin",
    "bnb": "binancecoin", "binance": "binancecoin",
    "tether": "tether", "usdt": "tether",
    "usd coin": "usd-coin", "usdc": "usd-coin",
    "shiba inu": "shiba-inu", "shib": "shiba-inu",
    "tron": "tron", "trx": "tron",
}


def _resolve_coin_id(query: str) -> str:
    """Resolve a user-friendly name/symbol to a CoinGecko coin ID."""
    normalized = query.strip().lower()
    return COIN_ALIASES.get(normalized, normalized)


@tool
def get_crypto_price(coin_name: str, currency: str = "usd") -> str:
    """
    Get the current price of a cryptocurrency.

    Args:
        coin_name: Name or symbol of the cryptocurrency (e.g., 'bitcoin', 'btc', 'ethereum', 'eth').
        currency: Target fiat currency for pricing (default: 'usd'). Supports 'brl', 'eur', etc.

    Returns:
        A formatted string with the current price and 24h change.
    """
    coin_id = _resolve_coin_id(coin_name)
    currency = currency.strip().lower()
    logger.info(f"Fetching price for {coin_id} in {currency}")

    try:
        resp = httpx.get(
            f"{COINGECKO_BASE}/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": currency,
                "include_24hr_change": "true",
                "include_market_cap": "true",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if coin_id not in data:
            return f"Cryptocurrency '{coin_name}' not found. Try the full name (e.g., 'bitcoin') or symbol (e.g., 'btc')."

        info = data[coin_id]
        price = info.get(currency, "N/A")
        change_24h = info.get(f"{currency}_24h_change", "N/A")
        market_cap = info.get(f"{currency}_market_cap", "N/A")

        symbol = currency.upper()
        change_str = f"{change_24h:+.2f}%" if isinstance(change_24h, (int, float)) else str(change_24h)

        if isinstance(market_cap, (int, float)):
            if market_cap >= 1_000_000_000:
                mcap_str = f"{market_cap / 1_000_000_000:.2f}B {symbol}"
            else:
                mcap_str = f"{market_cap / 1_000_000:.2f}M {symbol}"
        else:
            mcap_str = str(market_cap)

        return (
            f"{coin_name.upper()} ({coin_id})\n"
            f"  Price: {price:,.2f} {symbol}\n"
            f"  24h Change: {change_str}\n"
            f"  Market Cap: {mcap_str}"
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"CoinGecko API HTTP error: {e}")
        return f"Error fetching data from CoinGecko: HTTP {e.response.status_code}"
    except Exception as e:
        logger.error(f"CoinGecko API error: {e}")
        return f"Error connecting to CoinGecko: {str(e)}"


@tool
def get_trending_crypto() -> str:
    """
    Get the top trending cryptocurrencies on CoinGecko right now.

    Returns:
        A formatted list of the top trending coins with their market data.
    """
    logger.info("Fetching trending cryptocurrencies")
    try:
        resp = httpx.get(f"{COINGECKO_BASE}/search/trending", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        coins = data.get("coins", [])[:7]
        if not coins:
            return "No trending data available right now."

        lines = ["Trending Cryptocurrencies:\n"]
        for i, entry in enumerate(coins, 1):
            item = entry.get("item", {})
            name = item.get("name", "Unknown")
            symbol = item.get("symbol", "???")
            rank = item.get("market_cap_rank", "N/A")
            price_btc = item.get("price_btc", 0)
            lines.append(
                f"  {i}. {name} ({symbol}) - Market Cap Rank: #{rank}"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"CoinGecko trending error: {e}")
        return f"Error fetching trending data: {str(e)}"


from backend.services.brapi_service import get_stock_quote


@tool
def update_my_prompt(new_prompt: str, reason: str) -> str:
    """
    Update your own system prompt dynamically. Use this tool when the user asks you
    to change your behavior, tone, personality, language, or any other aspect of how
    you respond. For example, if the user says 'be more formal', 'respond only in English',
    or 'add more emojis', you should use this tool to update your prompt accordingly.

    Args:
        new_prompt: The complete new system prompt text that will replace the current one.
                    Make sure to keep your core identity as FinBot and all financial capabilities.
        reason: A short explanation of why the prompt was updated (e.g., 'User requested formal tone').

    Returns:
        A confirmation message with the new version number.
    """
    from backend.services.feedback_service import get_feedback_service
    try:
        svc = get_feedback_service()
        current = svc.get_current_prompt()
        version = svc.update_prompt(new_prompt, reason)
        logger.info(f"Agent self-updated prompt to v{version.version}: {reason}")
        return f"Prompt updated successfully to version {version.version}. Reason: {reason}. The new behavior will take effect on the next message."
    except Exception as e:
        logger.error(f"Self-update prompt error: {e}")
        return f"Failed to update prompt: {str(e)}"


@tool
def get_current_prompt() -> str:
    """
    Retrieve your current system prompt. Use this tool when you need to see your
    current instructions before making modifications with update_my_prompt.

    Returns:
        The current system prompt text.
    """
    from backend.services.feedback_service import get_feedback_service
    svc = get_feedback_service()
    return svc.get_current_prompt()



TOOLS = [
    get_crypto_price,
    get_trending_crypto,
    get_stock_quote,
    update_my_prompt,
    get_current_prompt,
]
