import os
import stripe
import logging
from fastapi import HTTPException

logger = logging.getLogger("stripe_webhook")
logger.setLevel(logging.INFO)

# Environment variables
STRIPE_API_KEY = os.getenv("STRIPE_SECRET")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Configure Stripe library
if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY
else:
    logger.warning("STRIPE_SECRET not set. Stripe API operations may fail.")


class InvalidStripeSignature(Exception):
    pass


def verify_and_parse_event(payload: bytes, signature_header: str):
    """
    Validate webhook signature and return parsed Stripe event.
    """
    if not signature_header:
        raise InvalidStripeSignature("Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature_header,
            STRIPE_WEBHOOK_SECRET
        )
        return event
    except Exception as e:
        logger.error(f"Stripe signature verification failed: {e}")
        raise InvalidStripeSignature(f"Invalid Stripe signature: {e}")
