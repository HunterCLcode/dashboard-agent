from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import query

app = FastAPI(title="Dashboard Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# KPIs  —  GET /kpis
# =============================================================================

@app.get("/kpis")
def get_kpis():
    row = query("""
        SELECT
            COUNT(DISTINCT order_id)       AS total_orders,
            ROUND(SUM(payment_value), 2)   AS total_revenue,
            ROUND(AVG(review_score), 2)    AS avg_review_score
        FROM order_facts
    """)[0]

    top = query("""
        SELECT category_en
        FROM order_facts
        WHERE category_en IS NOT NULL
        GROUP BY category_en
        ORDER BY SUM(price) DESC
        LIMIT 1
    """)

    return {
        "total_orders":      row["total_orders"],
        "total_revenue":     row["total_revenue"],
        "avg_review_score":  row["avg_review_score"],
        "top_category":      top[0]["category_en"] if top else "N/A",
    }


# =============================================================================
# Charts  —  GET /charts/{endpoint}
# =============================================================================

CHART_CONFIGS: dict[str, dict] = {
    "revenue-over-time": {
        "sql": """
            SELECT strftime('%Y-%m', order_date) AS month,
                   ROUND(SUM(payment_value), 2)  AS revenue
            FROM order_facts
            WHERE order_date IS NOT NULL
            GROUP BY month
            ORDER BY month
        """,
        "chart_type":  "line",
        "x_key":       "month",
        "y_key":       "revenue",
        "title":       "Revenue Over Time",
    },
    "orders-by-state": {
        "sql": """
            SELECT customer_state,
                   COUNT(DISTINCT order_id) AS order_count
            FROM order_facts
            WHERE customer_state IS NOT NULL
            GROUP BY customer_state
            ORDER BY order_count DESC
        """,
        "chart_type":  "map",
        "x_key":       "customer_state",
        "y_key":       "order_count",
        "title":       "Orders by State",
    },
    "top-categories": {
        "sql": """
            SELECT category_en,
                   ROUND(SUM(price), 2) AS revenue
            FROM order_facts
            WHERE category_en IS NOT NULL
            GROUP BY category_en
            ORDER BY revenue DESC
            LIMIT 10
        """,
        "chart_type":  "bar",
        "x_key":       "category_en",
        "y_key":       "revenue",
        "title":       "Top Product Categories",
        "orientation": "horizontal",
    },
    "review-distribution": {
        "sql": """
            SELECT CAST(review_score AS TEXT) AS score,
                   COUNT(*) AS count
            FROM order_facts
            WHERE review_score IS NOT NULL
            GROUP BY review_score
            ORDER BY review_score
        """,
        "chart_type":  "bar",
        "x_key":       "score",
        "y_key":       "count",
        "title":       "Review Score Distribution",
    },
    "delivery-delay-by-state": {
        "sql": """
            SELECT customer_state,
                   ROUND(AVG(delivery_delay_days), 1) AS avg_delay_days
            FROM order_facts
            WHERE delivery_delay_days IS NOT NULL
              AND customer_state IS NOT NULL
            GROUP BY customer_state
            ORDER BY avg_delay_days DESC
            LIMIT 15
        """,
        "chart_type":  "bar",
        "x_key":       "customer_state",
        "y_key":       "avg_delay_days",
        "title":       "Delivery Delay by State (avg days)",
        "orientation": "horizontal",
    },
    "payment-methods": {
        "sql": """
            SELECT payment_type,
                   COUNT(*) AS count
            FROM order_facts
            WHERE payment_type IS NOT NULL
            GROUP BY payment_type
            ORDER BY count DESC
        """,
        "chart_type":  "pie",
        "x_key":       "payment_type",
        "y_key":       "count",
        "title":       "Payment Methods",
    },
}


@app.get("/charts/{endpoint}")
def get_chart(endpoint: str):
    if endpoint not in CHART_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Unknown chart endpoint: {endpoint}")

    cfg = CHART_CONFIGS[endpoint]
    data = query(cfg["sql"])

    return {
        "data":        data,
        "chart_type":  cfg["chart_type"],
        "x_key":       cfg["x_key"],
        "y_key":       cfg["y_key"],
        "title":       cfg["title"],
        "orientation": cfg.get("orientation"),
    }


# =============================================================================
# Agent  —  POST /query
# Wire up your NL2SQL agent in this function.
# =============================================================================

class QueryRequest(BaseModel):
    query: str


@app.post("/query")
def post_query(body: QueryRequest):
    # TODO: replace this stub with your NL2SQL agent call
    return {
        "summary":    f'Received: "{body.query}". NL2SQL agent not yet wired up — implement it here.',
        "sql":        None,
        "data":       None,
        "chart_type": None,
        "x_key":      None,
        "y_key":      None,
        "title":      None,
        "orientation": None,
    }
