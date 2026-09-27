import duckdb
import json
import yfinance as yf
import pandas as pd
from datetime import datetime

DB_PATH = "finagent.duckdb"

def init_db():
    """Initialize DuckDB cache and market price tables."""
    conn = duckdb.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_cache (
            ticker VARCHAR,
            agent_type VARCHAR,
            created_date VARCHAR,
            response_json VARCHAR,
            PRIMARY KEY (ticker, agent_type, created_date)
        );
        CREATE TABLE IF NOT EXISTS daily_prices (
            ticker VARCHAR,
            date DATE,
            close DOUBLE,
            PRIMARY KEY (ticker, date)
        );
    """)
    conn.close()

def get_cached_analysis(ticker: str, agent_type: str, date_str: str):
    """Retrieve analysis result from DuckDB cache to save LLM quota."""
    conn = duckdb.connect(DB_PATH, read_only=True)
    res = conn.execute("""
        SELECT response_json FROM agent_cache 
        WHERE ticker = ? AND agent_type = ? AND created_date = ?
    """, (ticker, agent_type, date_str)).fetchone()
    conn.close()
    return json.loads(res[0]) if res else None

def save_agent_cache(ticker: str, agent_type: str, date_str: str, response: dict):
    """Store agent analysis response into DuckDB cache."""
    conn = duckdb.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO agent_cache VALUES (?, ?, ?, ?)
    """, (ticker, agent_type, date_str, json.dumps(response)))
    conn.close()

def sync_price_data(ticker: str, conn, period: str = "1y"):
    """Fetch daily price history via yfinance and store into DuckDB if needed."""
    count = conn.execute(
        "SELECT COUNT(*) FROM daily_prices WHERE ticker = ?", (ticker,)
    ).fetchone()[0]
    
    if count < 50:  # Fetch if missing or insufficient historical data
        df = yf.download(ticker, period=period, progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df = df.reset_index()
            df.columns = [str(col).lower() for col in df.columns]
            if 'date' in df.columns and 'close' in df.columns:
                df = df[['date', 'close']]
                df['ticker'] = ticker
                
                conn.register("temp_prices", df)
                conn.execute("""
                    INSERT OR REPLACE INTO daily_prices 
                    SELECT ticker, CAST(date AS DATE), close FROM temp_prices
                """)

def calculate_quant_metrics(ticker: str, benchmark_ticker: str = "SPY") -> dict:
    """
    Calculate quantitative indicators using DuckDB SQL and yfinance market data.
    Metrics:
    - Sharpe Ratio (Annualized)
    - Max Drawdown
    - Value at Risk 95% (VaR 95)
    - Beta (relative to benchmark e.g., SPY)
    - Risk Level Categorization
    """
    init_db()
    conn = duckdb.connect(DB_PATH)
    try:
        # Sync stock and market benchmark (SPY) price history into DuckDB
        sync_price_data(ticker, conn)
        sync_price_data(benchmark_ticker, conn)

        # Compute return metrics, max drawdown, VaR 95, and Beta using DuckDB SQL
        query = """
        WITH raw_prices AS (
            SELECT ticker, date, close,
                   LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS prev_close
            FROM daily_prices
            WHERE ticker IN (?, ?)
        ),
        daily_returns AS (
            SELECT ticker, date, close,
                   (close - prev_close) / prev_close AS ret,
                   MAX(close) OVER (
                       PARTITION BY ticker 
                       ORDER BY date 
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                   ) AS peak
            FROM raw_prices
            WHERE prev_close IS NOT NULL
        ),
        asset_stats AS (
            SELECT 
                ticker,
                (AVG(ret) / NULLIF(STDDEV_SAMP(ret), 0)) * SQRT(252) AS sharpe_ratio,
                MAX((peak - close) / peak) AS max_drawdown,
                ABS(QUANTILE_CONT(ret, 0.05)) AS var_95
            FROM daily_returns
            WHERE ticker = ?
            GROUP BY ticker
        ),
        beta_stat AS (
            SELECT 
                COVAR_SAMP(t.ret, b.ret) / NULLIF(VAR_SAMP(b.ret), 0) AS beta
            FROM (SELECT date, ret FROM daily_returns WHERE ticker = ?) t
            JOIN (SELECT date, ret FROM daily_returns WHERE ticker = ?) b
              ON t.date = b.date
        )
        SELECT 
            a.sharpe_ratio,
            a.max_drawdown,
            a.var_95,
            b.beta
        FROM asset_stats a, beta_stat b;
        """
        
        row = conn.execute(query, (ticker, benchmark_ticker, ticker, ticker, benchmark_ticker)).fetchone()
        
        if not row or row[0] is None:
            return {
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "var_95": 0.0,
                "beta": 1.0,
                "risk_level": "UNKNOWN"
            }

        sharpe_ratio = float(row[0]) if row[0] is not None else 0.0
        max_drawdown = float(row[1]) if row[1] is not None else 0.0
        var_95 = float(row[2]) if row[2] is not None else 0.0
        beta = float(row[3]) if row[3] is not None else 1.0

        # Categorize risk level based on Drawdown and Beta
        if max_drawdown > 0.30 or beta > 1.5:
            risk_level = "HIGH"
        elif max_drawdown > 0.15 or beta > 1.1:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 4),
            "var_95": round(var_95, 4),
            "beta": round(beta, 2),
            "risk_level": risk_level
        }

    except Exception as e:
        return {
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "var_95": 0.0,
            "beta": 1.0,
            "risk_level": "ERROR",
            "error_detail": str(e)
        }
    finally:
        conn.close()