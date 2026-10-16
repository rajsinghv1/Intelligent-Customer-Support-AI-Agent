
from app.agents.classifier_agent import (
    classify_customer_message,
    ClassificationError,
)


def analyze_customer_message(message: str) -> dict:
    """
    Analyze a customer message using Gemini.

    Returns:
        intent
        sentiment
        urgency
        requires_ticket
        summary
    """

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Customer message cannot be empty.")

    return classify_customer_message(message)


def get_priority_label(urgency: str) -> str:
    labels = {
        "low": "Low Priority",
        "medium": "Medium Priority",
        "high": "High Priority",
    }

    return labels.get(urgency, "Unknown Priority")


def should_create_ticket(classification: dict) -> bool:
    return classification.get("requires_ticket") is True
