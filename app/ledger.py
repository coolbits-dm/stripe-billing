import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional

from .db import LedgerEntry, get_db_session

logger = logging.getLogger("ledger")


# --------------------------
# TOP-UP EVENTS (Stripe → cbT)
# --------------------------

def record_topup_event(event: Dict[str, Any]) -> str:
    """
    Records a Stripe top-up event:
    {
        "wallet_id": str,
        "amount_cbT": float,
        "source": "stripe_payment_intent",
        "payment_intent_id": str,
        "amount_eur": float,
        "metadata": dict,
    }
    """
    db = get_db_session()

    try:
        entry = LedgerEntry(
            ref=event["wallet_id"],
            delta=Decimal(abs(event["amount_cbT"])),
            reason="Stripe top-up",
            meta=event,
        )

        db.add(entry)
        db.commit()

        logger.info(
            f"[LEDGER] TOP-UP wallet={event['wallet_id']} +{event['amount_cbT']} cT"
        )

        return str(entry.id)

    except Exception as e:
        logger.error(f"[LEDGER] Failed top-up: {e}")
        db.rollback()
        raise

    finally:
        db.close()


# --------------------------
# USAGE EVENTS (cbT cost → negative)
# --------------------------

def record_usage_event(event: Dict[str, Any]) -> str:
    """
    {
        "wallet_id": str,
        "amount_cbT": float,
        "reason": str,
        "meta": {}
    }
    """
    db = get_db_session()

    try:
        entry = LedgerEntry(
            ref=event["wallet_id"],
            delta=Decimal(-abs(event["amount_cbT"])),
            reason=event.get("reason", "usage"),
            meta=event.get("meta", {}),
        )

        db.add(entry)
        db.commit()

        logger.info(
            f"[LEDGER] USAGE wallet={event['wallet_id']} -{event['amount_cbT']} cT"
        )

        return str(entry.id)

    except Exception as e:
        logger.error(f"[LEDGER] Failed usage event: {e}")
        db.rollback()
        raise

    finally:
        db.close()


# --------------------------
# FAILED EVENTS (retry/disaster logs)
# --------------------------

def record_failed_event(source: str, payload: dict, error: str):
    db = get_db_session()

    try:
        entry = LedgerEntry(
            ref=f"failed::{source}",
            delta=Decimal(0),
            reason=f"FAILED::{source}",
            meta={"payload": payload, "error": error, "ts": datetime.utcnow().isoformat()},
        )

        db.add(entry)
        db.commit()

        logger.warning(f"[LEDGER] Failed event logged: {source}")

    except Exception as e:
        logger.error(f"[LEDGER] Failed to write failure log: {e}")
        db.rollback()
        raise

    finally:
        db.close()


# --------------------------
# BALANCE
# --------------------------

def get_wallet_balance(wallet_id: str) -> float:
    """Sum positive and negative deltas."""
    db = get_db_session()

    try:
        from sqlalchemy import func

        total = (
            db.query(func.sum(LedgerEntry.delta))
            .filter(LedgerEntry.ref == wallet_id)
            .scalar()
        )

        return float(total or 0)

    except Exception as e:
        logger.error(f"[LEDGER] Balance error for {wallet_id}: {e}")
        return 0.0

    finally:
        db.close()
