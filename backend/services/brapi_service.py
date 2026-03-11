"""
Brapi API integration for B3 stocks and market data.
"""
import httpx
from langchain_core.tools import tool
from loguru import logger
from backend.config import get_settings

BRAPI_BASE = "https://brapi.dev/api"

@tool
def get_stock_quote(symbols: str) -> str:
    """
    Get the current prices and details for one or more B3 stocks, ETFs, or indices.
    
    Args:
        symbols: One or more ticker symbols separated by commas (e.g., 'PETR4', 'VALE3', 'PETR4,VALE3,IBOV').
    
    Returns:
        A formatted string with the current prices, changes, and basic info for each asset.
    """
    settings = get_settings()
    token = settings.brapi_api_key
    
    clean_symbols = ",".join([s.strip().upper() for s in symbols.split(",") if s.strip()])
    logger.info(f"Fetching Brapi quotes for: {clean_symbols}")
    
    try:
        resp = httpx.get(
            f"{BRAPI_BASE}/quote/{clean_symbols}",
            params={"token": token},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        
        results = data.get("results", [])
        if not results:
            return f"Quotes for symbols '{symbols}' not found on Brapi. Make sure they are valid B3 tickers."
        
        lines = ["B3 Market Quotes:\n"]
        for stock in results:
            symbol = stock.get("symbol", "???")
            price = stock.get("regularMarketPrice", "N/A")
            change = stock.get("regularMarketChangePercent", "N/A")
            name = stock.get("longName", stock.get("shortName", symbol))
            currency = stock.get("currency", "BRL")
            
            price_str = f"{price:,.2f}" if isinstance(price, (int, float)) else str(price)
            change_str = f"{change:+.2f}%" if isinstance(change, (int, float)) else str(change)
            
            lines.append(
                f"  • {name} ({symbol}): {price_str} {currency} ({change_str})"
            )
            
        return "\n".join(lines)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Brapi API HTTP error: {e}")
        return f"Error fetching Brapi data: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Brapi API error: {e}")
        return f"Error connecting to Brapi or parsing data: {str(e)}"
