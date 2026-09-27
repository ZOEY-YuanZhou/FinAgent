from langgraph.graph import StateGraph, START, END
from src.agents.state import PortfolioState
from src.agents.quant_agent import run_quant
from src.agents.fundamental_agent import run_fundamental
from src.agents.sentiment_agent import run_sentiment
from src.agents.supervisor_agent import run_supervisor

builder = StateGraph(PortfolioState)

# Register execution nodes
builder.add_node("quant", run_quant)
builder.add_node("fundamental", run_fundamental)
builder.add_node("sentiment", run_sentiment)
builder.add_node("supervisor", run_supervisor)

# Stagger node execution sequentially to protect API quota (prevent 429 errors)
builder.add_edge(START, "quant")
builder.add_edge("quant", "fundamental")
builder.add_edge("fundamental", "sentiment")
builder.add_edge("sentiment", "supervisor")
builder.add_edge("supervisor", END)

portfolio_graph = builder.compile()
