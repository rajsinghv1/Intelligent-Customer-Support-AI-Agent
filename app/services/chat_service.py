
from app.core.llm import generate_ai_response
from app.database.db import (
    get_messages,
    save_message,
    update_conversation_title,
)
from app.rag.rag_service import answer_with_rag
from app.rag.vector_store import vector_store_exists


MAX_HISTORY_MESSAGES = 20


def process_customer_message(
    conversation_id,
    user_message,
    use_rag=True,
):
    user_message = user_message.strip()

    if not user_message:
        raise ValueError(
            "Customer message cannot be empty."
        )

    previous_messages = get_messages(
        conversation_id
    )

    history = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in previous_messages[
            -MAX_HISTORY_MESSAGES:
        ]
    ]

    save_message(
        conversation_id,
        "user",
        user_message,
    )

    if not previous_messages:
        update_conversation_title(
            conversation_id,
            user_message[:60],
        )

    return _generate_and_save(
        conversation_id,
        user_message,
        history,
        use_rag,
    )


def _generate_and_save(
    conversation_id,
    question,
    history,
    use_rag,
):
    if use_rag and vector_store_exists():
        result = answer_with_rag(
            question,
            history=history,
        )

        response = result["answer"]

        if result["sources"]:
            response += "\n\n**Retrieved sources:**\n"

            seen = set()

            for source in result["sources"]:
                name = source["source"]
                page = source["page"]

                label = (
                    f"{name} (page {page})"
                    if page is not None
                    else name
                )

                if label not in seen:
                    response += f"- {label}\n"
                    seen.add(label)

    else:
        messages = history + [
            {
                "role": "user",
                "content": question,
            }
        ]

        response = generate_ai_response(
            messages
        )

    save_message(
        conversation_id,
        "assistant",
        response,
    )

    return response


def retry_last_message(
    conversation_id,
    use_rag=True,
):
    messages = get_messages(conversation_id)

    if not messages:
        raise ValueError(
            "No messages available."
        )

    if messages[-1]["role"] != "user":
        raise ValueError(
            "No pending AI response."
        )

    question = messages[-1]["content"]

    history = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages[
            -(MAX_HISTORY_MESSAGES + 1):-1
        ]
    ]

    return _generate_and_save(
        conversation_id,
        question,
        history,
        use_rag,
    )
