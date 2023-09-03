from .count_tokens_in_conversation import count_tokens_in_conversation
from .count_tokens import count_tokens

def would_exceed_limit(conversation, new_message, limit):
    return (
        count_tokens_in_conversation(conversation) + count_tokens(new_message) > limit
    )
