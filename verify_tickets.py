
import json

from app.database.ticket_db import init_ticket_db
from app.services.ticket_service import (
    process_customer_ticket,
    fetch_ticket,
    fetch_all_tickets,
    change_ticket_status,
    fetch_ticket_stats,
)


def show(data):
    print(json.dumps(data, indent=4, default=str))


def main():
    print("=" * 60)
    print("PHASE 3 PART 2 - SUPPORT TICKET SYSTEM")
    print("=" * 60)

    init_ticket_db()
    print("\nSQLite database initialized.")

    customer_id = "DEMO_CUSTOMER_001"

    message = (
        "My payment was deducted twice. "
        "Please resolve this urgently."
    )

    print("\nTEST 1 - Create support ticket")

    result = process_customer_ticket(
        customer_id,
        message,
    )
    show(result)

    ticket_id = result["ticket_id"]

    assert ticket_id is not None, (
        "Expected a ticket for the urgent payment complaint."
    )

    print("\nTEST 2 - Duplicate prevention")

    duplicate = process_customer_ticket(
        customer_id,
        message,
        classification=result["classification"],
    )
    show(duplicate)

    assert duplicate["ticket_id"] == ticket_id
    assert duplicate["ticket_created"] is False

    print("\nTEST 3 - Retrieve ticket")

    ticket = fetch_ticket(ticket_id)
    show(ticket)

    assert ticket is not None
    assert ticket["ticket_id"] == ticket_id

    print("\nTEST 4 - Update status")

    updated = change_ticket_status(
        ticket_id,
        "in_progress",
    )

    print("Updated:", updated)

    assert updated is True
    assert fetch_ticket(ticket_id)["status"] == "in_progress"

    print("\nTEST 5 - High priority tickets")

    high_priority = fetch_all_tickets(
        priority="high"
    )

    show(high_priority)

    print("\nTEST 6 - Ticket statistics")
    show(fetch_ticket_stats())

    print("\nTEST 7 - No ticket for positive feedback")

    positive = process_customer_ticket(
        "DEMO_CUSTOMER_002",
        "Thank you! Your service was excellent.",
    )

    show(positive)

    assert positive["ticket_created"] is False
    assert positive["ticket_id"] is None

    print("\n" + "=" * 60)
    print("ALL SUPPORT TICKET CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
