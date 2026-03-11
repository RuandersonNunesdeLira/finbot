"""
ChromaDB vector store for RAG retrieval.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from backend.config import get_settings


FINANCIAL_KNOWLEDGE: list[dict[str, str]] = [
    {
        "id": "btc_basics",
        "content": (
            "Bitcoin (BTC) is the first and most well-known cryptocurrency, created in 2009 by "
            "Satoshi Nakamoto. It operates on a decentralized blockchain network and is often referred "
            "to as 'digital gold'. Bitcoin has a fixed supply of 21 million coins, making it deflationary."
        ),
    },
    {
        "id": "eth_basics",
        "content": (
            "Ethereum (ETH) is a decentralized platform that enables smart contracts and decentralized "
            "applications (dApps). Created by Vitalik Buterin, it introduced the concept of programmable "
            "blockchain. Ethereum transitioned to Proof-of-Stake in 2022 with 'The Merge'."
        ),
    },
    {
        "id": "what_is_crypto",
        "content": (
            "Cryptocurrency is a digital or virtual form of currency that uses cryptography for security. "
            "Unlike traditional currencies, cryptocurrencies are decentralized and operate on blockchain technology. "
            "They can be used for investment, payments, and as a store of value."
        ),
    },
    {
        "id": "market_cap",
        "content": (
            "Market capitalization (market cap) in crypto is calculated by multiplying the current price "
            "of a coin by its total circulating supply. It's a key metric to evaluate the relative size "
            "and dominance of a cryptocurrency. Categories: Large-cap (>$10B), Mid-cap ($1-10B), Small-cap (<$1B)."
        ),
    },
    {
        "id": "defi_basics",
        "content": (
            "DeFi (Decentralized Finance) refers to financial services built on blockchain networks, "
            "eliminating intermediaries like banks. Key DeFi concepts include: Lending/Borrowing (Aave, Compound), "
            "Decentralized Exchanges or DEXs (Uniswap, SushiSwap), Yield Farming, and Liquidity Pools."
        ),
    },
    {
        "id": "stablecoins",
        "content": (
            "Stablecoins are cryptocurrencies pegged to a stable asset like the US Dollar. "
            "Examples include Tether (USDT), USD Coin (USDC), and DAI. They are widely used for trading, "
            "remittances, and as a safe haven during market volatility."
        ),
    },
    {
        "id": "crypto_risks",
        "content": (
            "Cryptocurrency investments carry significant risks: high volatility (prices can swing 10-20% daily), "
            "regulatory uncertainty, security risks (hacks, scams), and technological risks. "
            "Investors should only invest what they can afford to lose, diversify, and do thorough research (DYOR)."
        ),
    },
    {
        "id": "blockchain_basics",
        "content": (
            "A blockchain is a distributed, decentralized digital ledger that records transactions across "
            "multiple computers. Each block contains a list of transactions and is linked to the previous block "
            "via cryptographic hashing, forming an immutable chain. Consensus mechanisms like Proof-of-Work (PoW) "
            "and Proof-of-Stake (PoS) validate transactions."
        ),
    },
    {
        "id": "invest_strategies",
        "content": (
            "Common crypto investment strategies include: HODL (buy and hold long-term), "
            "Dollar-Cost Averaging or DCA (investing fixed amounts at regular intervals), "
            "Swing Trading (buying low and selling high over days/weeks), and Staking "
            "(locking up coins to earn rewards). Each strategy has different risk/reward profiles."
        ),
    },
    {
        "id": "nft_basics",
        "content": (
            "NFTs (Non-Fungible Tokens) are unique digital assets on the blockchain representing "
            "ownership of art, music, collectibles, and more. Unlike cryptocurrencies, each NFT is unique "
            "and cannot be exchanged one-to-one. Major NFT marketplaces include OpenSea and Blur."
        ),
    },
]


class VectorService:

    def __init__(self) -> None:
        settings = get_settings()
        try:
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
            logger.info(f"Connected to ChromaDB at {settings.chroma_host}:{settings.chroma_port}")
        except Exception:
            logger.warning("ChromaDB server not available, using in-memory client as fallback.")
            self._client = chromadb.Client()

        self._collection = self._client.get_or_create_collection(
            name="financial_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
        self._seed_knowledge()

    def _seed_knowledge(self) -> None:
        """Seed the vector store with initial financial knowledge if empty."""
        if self._collection.count() > 0:
            logger.info(f"Vector store already contains {self._collection.count()} documents.")
            return

        logger.info("Seeding vector store with financial knowledge base...")
        self._collection.add(
            ids=[doc["id"] for doc in FINANCIAL_KNOWLEDGE],
            documents=[doc["content"] for doc in FINANCIAL_KNOWLEDGE],
        )
        logger.info(f"Seeded {len(FINANCIAL_KNOWLEDGE)} documents into ChromaDB.")

    def query(self, text: str, n_results: int = 3) -> list[str]:
        try:
            results = self._collection.query(
                query_texts=[text],
                n_results=min(n_results, self._collection.count()),
            )
            documents = results.get("documents", [[]])[0]
            logger.debug(f"Vector store returned {len(documents)} results for query: '{text[:50]}...'")
            return documents
        except Exception as e:
            logger.error(f"Vector store query failed: {e}")
            return []

    def add_document(self, doc_id: str, content: str) -> None:
        """Add a new document to the vector store."""
        try:
            self._collection.add(ids=[doc_id], documents=[content])
            logger.info(f"Added document '{doc_id}' to vector store.")
        except Exception as e:
            logger.error(f"Failed to add document: {e}")



_vector_service: VectorService | None = None


def get_vector_service() -> VectorService:
    """Get or create the VectorService singleton."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
