
import csv
import io
from collections import Counter

import pandas as pd
import streamlit as st

from app.database.ticket_db import (
    get_ticket,
    get_ticket_stats,
    list_tickets,
    update_ticket_status,
)


STATUSES = [
    "open",
    "in_progress",
    "resolved",
    "closed",
]

PRIORITIES = [
    "high",
    "medium",
    "low",
]


def format_label(value):
    return str(value).replace("_", " ").title()


def build_csv(tickets):
    """Export selected tickets without internal hashes."""

    output = io.StringIO()
    writer = csv.writer(output)

    columns = [
        "ticket_id",
        "customer_id",
        "customer_message",
        "intent",
        "sentiment",
        "urgency",
        "priority",
        "status",
        "summary",
        "created_at",
        "updated_at",
    ]

    writer.writerow(columns)

    for ticket in tickets:
        writer.writerow([
            ticket.get(column, "")
            for column in columns
        ])

    return output.getvalue().encode("utf-8-sig")


def render_metrics():
    """Display counts from the SQLite database."""

    stats = get_ticket_stats()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total", stats["total"])
    col2.metric("Open", stats["open"])
    col3.metric("In Progress", stats["in_progress"])
    col4.metric("Resolved", stats["resolved"])
    col5.metric("Closed", stats["closed"])


def render_charts(tickets):
    """Display ticket distribution charts."""

    st.subheader("📊 Ticket Analytics")

    if not tickets:
        st.info("No tickets available for analytics.")
        return

    status_counts = Counter(
        ticket["status"] for ticket in tickets
    )

    priority_counts = Counter(
        ticket["priority"] for ticket in tickets
    )

    intent_counts = Counter(
        ticket["intent"] for ticket in tickets
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Tickets by Status**")

        status_df = pd.DataFrame({
            "Status": [
                format_label(status)
                for status in STATUSES
            ],
            "Tickets": [
                status_counts.get(status, 0)
                for status in STATUSES
            ],
        })

        st.bar_chart(
            status_df.set_index("Status")
        )

    with col2:
        st.markdown("**Tickets by Priority**")

        priority_df = pd.DataFrame({
            "Priority": [
                format_label(priority)
                for priority in PRIORITIES
            ],
            "Tickets": [
                priority_counts.get(priority, 0)
                for priority in PRIORITIES
            ],
        })

        st.bar_chart(
            priority_df.set_index("Priority")
        )

    st.markdown("**Tickets by Intent**")

    intent_df = pd.DataFrame([
        {
            "Intent": format_label(intent),
            "Tickets": count,
        }
        for intent, count in sorted(
            intent_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ])

    if not intent_df.empty:
        st.bar_chart(
            intent_df.set_index("Intent")
        )


def render_ticket_table(tickets):
    """Display filtered tickets as a table."""

    st.subheader("📋 Ticket Records")

    if not tickets:
        st.info("No matching tickets found.")
        return

    columns = [
        "ticket_id",
        "customer_id",
        "intent",
        "sentiment",
        "priority",
        "status",
        "created_at",
    ]

    df = pd.DataFrame(tickets)[columns].copy()

    df.columns = [
        "Ticket ID",
        "Customer",
        "Intent",
        "Sentiment",
        "Priority",
        "Status",
        "Created At",
    ]

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        "⬇️ Export Filtered Tickets (CSV)",
        data=build_csv(tickets),
        file_name="support_tickets.csv",
        mime="text/csv",
    )


def render_ticket_details(tickets):
    """Show details and allow status changes."""

    st.subheader("🎫 Ticket Details & Management")

    if not tickets:
        st.info("No tickets available to manage.")
        return

    ticket_ids = [
        ticket["ticket_id"]
        for ticket in tickets
    ]

    selected_id = st.selectbox(
        "Select Ticket",
        ticket_ids,
        key="dashboard_selected_ticket",
    )

    ticket = get_ticket(selected_id)

    if ticket is None:
        st.warning("Selected ticket no longer exists.")
        return

    with st.container(border=True):
        st.markdown(f"### {ticket['ticket_id']}")

        col1, col2, col3 = st.columns(3)

        col1.write(
            f"**Priority:** {format_label(ticket['priority'])}"
        )
        col2.write(
            f"**Status:** {format_label(ticket['status'])}"
        )
        col3.write(
            f"**Intent:** {format_label(ticket['intent'])}"
        )

        st.write("**Customer ID:**", ticket["customer_id"])
        st.write("**Customer Message:**")
        st.write(ticket["customer_message"])

        st.write("**AI Summary:**")
        st.write(ticket["summary"])

        st.write(
            "**Sentiment:**",
            format_label(ticket["sentiment"]),
        )

        st.caption(
            f"Created: {ticket['created_at']}"
        )
        st.caption(
            f"Last Updated: {ticket['updated_at']}"
        )

        st.divider()

        st.markdown("#### Update Ticket Status")

        selected_status = st.selectbox(
            "New Status",
            STATUSES,
            index=STATUSES.index(ticket["status"]),
            format_func=format_label,
            key=f"status_{selected_id}",
        )

        if st.button(
            "💾 Save Status",
            type="primary",
            key=f"save_{selected_id}",
        ):
            try:
                if selected_status == ticket["status"]:
                    st.info("Ticket already has this status.")
                else:
                    updated = update_ticket_status(
                        selected_id,
                        selected_status,
                    )

                    if updated:
                        st.success(
                            "Ticket status updated successfully."
                        )
                        st.rerun()
                    else:
                        st.error("Ticket update failed.")

            except Exception as exc:
                st.error(
                    f"Unable to update ticket: {exc}"
                )


def render_ticket_dashboard():
    """Main dashboard entry point."""

    st.title("🎫 Support Ticket Management")

    st.caption(
        "AI-powered ticket monitoring with SQLite."
    )

    if st.button("🔄 Refresh Dashboard"):
        st.rerun()

    st.divider()

    render_metrics()

    st.divider()

    st.subheader("🔎 Search & Filters")

    search_query = st.text_input(
        "Search tickets",
        placeholder=(
            "Search ticket ID, customer ID, "
            "message or summary"
        ),
    ).strip().casefold()

    col1, col2 = st.columns(2)

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + STATUSES,
            format_func=format_label,
        )

    with col2:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All"] + PRIORITIES,
            format_func=format_label,
        )

    # Current ticket_db.py supports up to 500
    # records per list_tickets() call.
    tickets = list_tickets(limit=500)

    if status_filter != "All":
        tickets = [
            ticket for ticket in tickets
            if ticket["status"] == status_filter
        ]

    if priority_filter != "All":
        tickets = [
            ticket for ticket in tickets
            if ticket["priority"] == priority_filter
        ]

    if search_query:
        tickets = [
            ticket
            for ticket in tickets
            if any(
                search_query in str(
                    ticket.get(field, "")
                ).casefold()
                for field in [
                    "ticket_id",
                    "customer_id",
                    "customer_message",
                    "summary",
                ]
            )
        ]

    st.caption(
        f"Showing {len(tickets)} matching tickets "
        "(search limited to latest 500 records)."
    )

    st.divider()

    render_charts(tickets)

    st.divider()

    render_ticket_table(tickets)

    st.divider()

    render_ticket_details(tickets)
