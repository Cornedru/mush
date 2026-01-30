"""
Correction processing module for Mario flag calculator.

This module handles the complete flow of analyzing a correction:
1. Fetch correction data from Yoshi
2. Calculate all flags
3. Post flag values back to Yoshi
4. Build and send webhook payload to kmb0t
"""

import json
from datetime import timezone
from zoneinfo import ZoneInfo

from tools.handle_requests import get_data, post_data
from tools.logger import log, INFO, WARN, ERROR
from tools.conf import YOSHI_URL, KMB0T_AUTH_TOKEN, KMB0T_URL
from tools.converters import parse_timestamp
from flags.calculator import calculate_flags


def format_timestamp(iso_string: str) -> str:
    """Convert ISO timestamp to Europe/Paris timezone."""
    if not iso_string:
        return ""
    try:
        dt = parse_timestamp(iso_string)
        if not dt:
            return iso_string
        dt_paris = dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Europe/Paris"))
        return dt_paris.isoformat().split("+")[0]
    except (ValueError, TypeError):
        return iso_string


def analyze_flags(flags: dict) -> dict:
    """Compute analysis metrics from flag results."""
    total = len(flags)
    triggered = sum(
        1 for f in flags.values()
        if isinstance(f, dict) and f.get("is_triggered")
    )
    score = sum(
        f["value"] for f in flags.values()
        if isinstance(f, dict) and "value" in f
    ) / total if total > 0 else 0

    suspicious = any(
        isinstance(f, dict) and f.get("is_triggered") and f.get("sufficient")
        for f in flags.values()
    )

    return {
        "suspicious": suspicious,
        "final_score": round(score, 4),
        "triggered_count": triggered,
        "total_flags": total,
        "flags": flags,
    }


def build_payload(correction: dict, correction_id: str, analysis: dict) -> dict:
    """Build structured webhook payload for kmb0t."""
    corrector = correction.get("corrector", {})
    push = correction.get("push", {})
    project = correction.get("project", {})

    payload = {
        "type": "mario",
        "correction": {
            "id": correction_id,
            "begin_at": format_timestamp(correction.get("begin_at")),
        },
        "corrector": {
            "id": corrector.get("id"),
            "login": corrector.get("login", "unknown"),
        },
        "correcteds": [
            {"id": c.get("id"), "login": c.get("login")}
            for c in push.get("correcteds", [])
            if isinstance(c, dict) and "login" in c
        ],
        "project": {
            "id": push.get("project_id") or project.get("correction_id"),
            "name": project.get("name"),
        },
        "analysis": analysis,
        "hash": KMB0T_AUTH_TOKEN,
    }

    return payload


def store_flags_in_yoshi(correction_id: str, flags: dict) -> bool:
    """Store calculated flags in Yoshi API."""
    try:
        flags_payload = []
        for flag_name, flag_data in flags.items():
            if isinstance(flag_data, dict) and "value" in flag_data:
                flag_entry = {
                    "correction_id": int(correction_id),
                    "flag_name": flag_name,
                    "value": flag_data["value"],
                    "is_triggered": flag_data.get("is_triggered", False),
                    "sufficient": flag_data.get("sufficient", False),
                    "description": flag_data.get("description", ""),
                }
                details = flag_data.get("details")
                if details is not None:
                    flag_entry["details"] = details
                flags_payload.append(flag_entry)

        if not flags_payload:
            log(WARN, "Flag Storage", f"No flags to store for correction {correction_id}")
            return False

        res = post_data(f"{YOSHI_URL}/flags/batch", json_data={"flags": flags_payload})
        if res and res.status_code < 400:
            log(INFO, "Flag Storage", f"Stored {len(flags_payload)} flags for correction {correction_id}")
            return True
        else:
            status = res.status_code if res else "no response"
            log(ERROR, "Flag Storage", f"Failed to store flags: HTTP {status}")
            return False
    except Exception as e:
        log(ERROR, "Flag Storage", f"Error storing flags for correction {correction_id}: {e}")
        return False


def send_webhook(payload: dict) -> None:
    """Send webhook payload to kmb0t."""
    correction_id = payload.get("correction", {}).get("id", {})
    try:
        res = post_data(f"{KMB0T_URL}/h/campus", json_data=payload)
        if not res or not hasattr(res, "status_code"):
            log(ERROR, "Webhook", f"Invalid response for correction {correction_id}")
        elif res.status_code >= 400:
            log(ERROR, "Webhook", f"Webhook failed with HTTP {res.status_code}")
        else:
            log(INFO, "Webhook", f"Webhook sent successfully (HTTP {res.status_code})")
    except Exception as e:
        log(ERROR, "Webhook", f"Error sending webhook: {e}")


def process_correction(correction_id: str) -> dict | None:
    """
    Process a correction and calculate all suspicion flags.

    Args:
        correction_id: The ID of the correction to process

    Returns:
        Dictionary of flag results, or None if processing failed
    """
    # Fetch correction
    correction = get_data(f"{YOSHI_URL}/corrections/{correction_id}")
    if not correction:
        log(ERROR, "Flag Processing", f"Failed to fetch correction {correction_id}")
        return None

    if not correction.get("begin_at"):
        log(WARN, "Flag Processing", f"Correction {correction_id} cancelled by moulinette")
        return None

    flags = calculate_flags(correction_id)
    if not flags:
        log(ERROR, "Flag Processing", f"Failed to calculate flags for correction {correction_id}")
        return None

    store_flags_in_yoshi(correction_id, flags)

    analysis = analyze_flags(flags)

    log(INFO, "Flag Processing",
        f"Correction {correction_id}: score={analysis['final_score']:.3f}, "
        f"triggered={analysis['triggered_count']}/{analysis['total_flags']}")

    payload = build_payload(correction, correction_id, analysis)
    send_webhook(payload)

    return flags
