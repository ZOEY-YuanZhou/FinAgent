from pydantic import BaseModel, Field
from src.agents.fundamental_agent import get_llm
from src.data_engine.ingester import get_cached_analysis, save_agent_cache


class SentimentAnalysisResult(BaseModel):
    """Pydantic schema for structured sentiment analysis output."""
    summary: str = Field(
        description="Comprehensive summary of recent news, macro sentiment, and market narrative."
    )
    sentiment_score: float = Field(
        description="Quantified market sentiment score bounded between -1.0 (extremely bearish) and 1.0 (extremely bullish), with 0.0 being neutral."
    )


def run_sentiment(state: dict) -> dict:
    """Sentiment agent for evaluating market news and macro sentiment."""
    ticker = state["ticker"]
    as_of_date = state.get("as_of_date", "2026-01-01")

    # Check local cache first to prevent redundant LLM API calls
    cached = get_cached_analysis(ticker, "sentiment", as_of_date)
    if cached:
        return {"sentiment_analysis": cached}

    # Bind LLM with Pydantic structured output schema
    llm = get_llm()
    structured_llm = llm.with_structured_output(SentimentAnalysisResult)

    prompt = f"""
    Evaluate recent market news, macro economic factors, and trader sentiment for ticker {ticker} as of {as_of_date}.
    Provide a clear summary of the overall market narrative and evaluate an objective sentiment score between -1.0 and 1.0.
    """

    # Invoke structured LLM and convert Pydantic object to dictionary
    analysis: SentimentAnalysisResult = structured_llm.invoke(prompt)
    result = analysis.model_dump()

    # Save structured result to local DuckDB cache and return incremental state update
    save_agent_cache(ticker, "sentiment", as_of_date, result)
    return {"sentiment_analysis": result}