import os
import logging
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse

from app import stripe_webhook, billing, ledger

app = FastAPI(title="Stripe Billing Microservice", version="1.0.0")

logger = logging.getLogger("stripe-billing")


@app.get("/api/health")
async def health():
    return {"ok": True, "service": "stripe-billing"}


# --------------------------
# STRIPE WEBHOOK ENDPOINT
# --------------------------

@app.post("/webhook/stripe")
async def webhook_stripe(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    payload = await request.body()

    # Step 1: verify signature
    try:
        event = stripe_webhook.verify_and_parse_event(
            payload=payload,
            signature_header=stripe_signature
        )
    except stripe_webhook.InvalidStripeSignature as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 2: route event → billing handler
    try:
        result = billing.handle_stripe_event(event)
    except Exception as e:
        ledger.record_failed_event("stripe_webhook", event, str(e))
        raise HTTPException(status_code=500, detail="Billing error")

    return JSONResponse({"ok": True, "result": result})


# --------------------------
# USAGE EVENTS (orchestrator → billing)
# --------------------------

@app.post("/api/v1/wallet/usage")
async def usage_event(event: dict):
    """
    Receives:
    {
        "wallet_id": "...",
        "amount_cbT": 2.14,
        "reason": "council_synthesis",
        "meta": {...}
    }
    """
    try:
        ledger.record_usage_event(event)
    except Exception as e:
        ledger.record_failed_event("usage", event, str(e))
        raise HTTPException(status_code=500, detail="Failed to write usage event")

    return {"ok": True}


# --------------------------
# WALLET BALANCE
# --------------------------

@app.get("/api/v1/wallet/balance/{wallet_id}")
async def balance(wallet_id: str):
    bal = ledger.get_wallet_balance(wallet_id)
    return {"wallet_id": wallet_id, "balance_cbT": bal}


# --------------------------
# TOP-UP (optional)
# --------------------------

@app.post("/api/v1/wallet/topup")
async def topup(event: dict):
    """
    Reserved for internal usage (Stripe webhook does this automatically)
    """
    try:
        ledger.record_topup_event(event)
    except Exception as e:
        ledger.record_failed_event("topup", event, str(e))
        raise HTTPException(status_code=500, detail="Top-up error")

    return {"ok": True}


# Run locally only
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
