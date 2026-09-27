from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.rate_limiters import InMemoryRateLimiter
from src.data_engine.ingester import get_cached_analysis, save_agent_cache

# Primary rate limiter: allows ~3.75 RPM (1 request every ~16 seconds)
primary_rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.06,
    check_every_n_seconds=0.1,
    max_bucket_size=1
)

# Backup rate limiter: isolated from primary token bucket to avoid lockouts during failover
backup_rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.06,
    check_every_n_seconds=0.1,
    max_bucket_size=1
)


def get_llm():
    """Shared LLM factory configured with rate limiting, fail-fast retries, and model fallbacks."""
    # 1. Primary Model: Set max_retries to 0 for immediate failover upon 429/503 errors
    primary_llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        rate_limiter=primary_rate_limiter,
        max_retries=0,
        request_timeout=30
    )

    # 2. Backup Model: Uses a separate rate limiter to prevent token deadlock during failover
    backup_llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        rate_limiter=backup_rate_limiter,
        max_retries=2,
        request_timeout=30
    )

    # 3. Chain primary model with backup fallback
    return primary_llm.with_fallbacks(
        [backup_llm],
        exceptions_to_handle=(Exception,)
    )


def run_fundamental(state: dict) -> dict:
    """Fundamental agent for analyzing financial statements and SEC filings."""
    ticker = state["ticker"]
    as_of_date = state.get("as_of_date", "2026-01-01")

    # Check DuckDB local cache first to conserve LLM quota
    cached = get_cached_analysis(ticker, "fundamental", as_of_date)
    if cached:
        return {"fundamental_data": cached}

    # Obtain LLM Runnable configured with automatic fallback
    llm = get_llm()
    prompt = f"Analyze fundamental performance for {ticker}. Provide key takeaways on revenue growth, profit margin, and debt risks."

    # Execute request; automatically falls back if primary model throws an exception
    response = llm.invoke(prompt)

    result = {"summary": response.content, "score": 8.5}
    save_agent_cache(ticker, "fundamental", as_of_date, result)
    return {"fundamental_data": result}