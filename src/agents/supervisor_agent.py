from src.agents.fundamental_agent import get_llm

def run_supervisor(state: dict) -> dict:
    """CIO node aggregating multi-agent signals into a final investment verdict."""
    llm = get_llm()
    prompt = f"""
You are the Chief Investment Officer. synthesize the multi-agent outputs below and produce a final decision:

- Quant Signals: {state.get('quant_signals')}
- Fundamental Analysis: {state.get('fundamental_data')}
- Sentiment Analysis: {state.get('sentiment_analysis')}

Provide:
1. Recommendation (BUY / HOLD / SELL)
2. Target Portfolio Allocation (%)
3. Key Thesis and Primary Risks
"""
    response = llm.invoke(prompt)
    return {"final_decision": {"recommendation": response.content}}
