
from app.database.ticket_db import (
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket_status,
    get_ticket_stats,
)

from app.services.classification_service import (
    analyze_customer_message,
    should_create_ticket,
)


def process_customer_ticket(
    customer_id,
    customer_message,
    classification=None,
):
    """
    Classify customer message and create a support
    ticket only when recommended.

    Existing classification can be supplied to
    avoid an additional Gemini API call.
    """

    if not isinstance(customer_id, str) or not customer_id.strip():
        raise ValueError("Customer ID is required.")

    if (
        not isinstance(customer_message, str)
        or not customer_message.strip()
    ):
        raise ValueError("Customer message is required.")

    if classification is None:
        classification = analyze_customer_message(
            customer_message
        )

    if not should_create_ticket(classification):
        return {
            "ticket_created": False,
            "ticket_id": None,
            "reason": "Ticket not required",
            "classification": classification,
        }

    result = create_ticket(
        customer_id=customer_id,
        customer_message=customer_message,
        classification=classification,
    )

    return {
        "ticket_created": result["created"],
        "ticket_id": result["ticket_id"],
        "reason": result["reason"],
        "classification": classification,
    }


def fetch_ticket(ticket_id):
    return get_ticket(ticket_id)


def fetch_all_tickets(
    status=None,
    priority=None,
    limit=100,
):
    return list_tickets(
        status=status,
        priority=priority,
        limit=limit,
    )


def change_ticket_status(ticket_id, status):
    return update_ticket_status(ticket_id, status)


def fetch_ticket_stats():
    return get_ticket_stats()
