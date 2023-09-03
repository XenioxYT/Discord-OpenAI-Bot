from .count_tokens import count_tokens

def count_tokens_in_conversation(conversation):
    return sum(count_tokens(m["content"]) for m in conversation)