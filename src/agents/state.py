import operator
from typing import TypedDict, Annotated, Dict, Any, List

class PortfolioState(TypedDict):
    """Global state schema for the multi-agent investment workflow."""
    ticker: str                             # Target asset symbol (e.g., NVDA, AAPL)
    as_of_date: str                         # Analysis reference date (YYYY-MM-DD)
    quant_signals: Dict[str, Any]            # Quantitative risk and momentum metrics
    fundamental_data: Dict[str, Any]         # Fundamental analysis results
    sentiment_analysis: Dict[str, Any]       # Market news and macro sentiment scores
    final_decision: Dict[str, Any]           # Portfolio allocation and verdict from CIO
    messages: Annotated[List[Any], operator.add]  # Traces and execution logs
