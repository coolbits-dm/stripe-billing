import logging
from . import ledger

logger = logging.getLogger("billing")


def handle_stripe_event(event: dict):
    """
    Stripe event router for microservice.
    Receives parsed Stripe event (already signature-verified).
    """

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    logger.info(f"Received Stripe event: {event_type}")

    # Handle PaymentIntent succeeded -> top-up
    if event_type == "payment_intent.succeeded":
        return _handle_payment_intent_succeeded(data)

    # Placeholder for future events (invoice.paid, customer.subscription, etc.)
    logger.info(f"Ignored Stripe event type: {event_type}")
    return {"ignored": event_type}


def _handle_payment_intent_succeeded(obj: dict):
    """
    Convert payment intent amount to cbT and write to ledger.
    """
    wallet_id = obj.get("metadata", {}).get("user_id", "anonymous")

    # amount_received is in cents → convert to EUR
    amount_eur = obj.get("amount_received", 0) / 100
    amount_cbT = round(amount_eur * 100, 2)  # 1 EUR = 100 cT

    # Prepare event payload for ledger
    payload = {
        "wallet_id": wallet_id,
        "amount_cbT": amount_cbT,
        "source": "stripe_payment_intent",
        "payment_intent_id": obj.get("id"),
        "amount_eur": amount_eur,
        "metadata": obj,
    }

    # Write to ledger
    try:
        ledger.record_topup_event(payload)
        logger.info(f"Top-up success: wallet={wallet_id}, +{amount_cbT} cT ({amount_eur} EUR)")
    except Exception as e:
        logger.error(f"Failed to record top-up: {e}")
        raise

    return {
        "wallet_id": wallet_id,
        "amount_cbT": amount_cbT,
        "amount_eur": amount_eur,
        "status": "top_up_recorded",
    }
