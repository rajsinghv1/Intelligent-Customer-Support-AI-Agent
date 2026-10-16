
import json

from app.services.classification_service import (
    analyze_customer_message,
    get_priority_label,
    should_create_ticket,
)


def main():
    print("=" * 60)
    print("PHASE 3 - CUSTOMER MESSAGE CLASSIFICATION")
    print("=" * 60)

    examples = [
        "Where is my order? It has been delayed for 10 days.",

        "I want a refund because the product arrived damaged.",

        "Thank you! Your service was excellent.",

        "My payment was deducted twice. Please resolve this urgently.",

        "What is the warranty period for your products?",
    ]

    for index, message in enumerate(examples, start=1):
        print(f"\nTEST {index}")
        print("-" * 60)
        print("Customer:", message)

        try:
            result = analyze_customer_message(message)

            print(
                json.dumps(
                    result,
                    indent=4,
                    ensure_ascii=False,
                )
            )

            print(
                "Priority:",
                get_priority_label(result["urgency"]),
            )

            print(
                "Ticket recommended:",
                should_create_ticket(result),
            )

        except Exception as exc:
            print("ERROR:", exc)

    print("\nVerification run finished.")


if __name__ == "__main__":
    main()
