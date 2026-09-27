from src.data_engine.ingester import calculate_quant_metrics

def run_quant(state: dict) -> dict:
    """Quantitative analysis node running pure algorithmic computation without LLM calls."""
    ticker = state["ticker"]
    metrics = calculate_quant_metrics(ticker)
    return {"quant_signals": metrics}
