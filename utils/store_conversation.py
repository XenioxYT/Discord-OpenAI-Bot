import json
import sqlite3
from .count_tokens_in_conversation import count_tokens_in_conversation

db_conn = sqlite3.connect('conversations.db')
db_conn.execute("""
CREATE TABLE IF NOT EXISTS conversations
    (conversation_id INTEGER PRIMARY KEY,
    conversation TEXT,
    is_busy BOOLEAN)
""")

def ensure_system_message_on_top(conversation):
    """Ensure the system message is the first message in the conversation."""
    if conversation and conversation[0]["role"] != "system":
        # Find the system message
        system_msg_idx = next((idx for idx, m in enumerate(conversation) if m["role"] == "system"), None)
        
        # If a system message is found and it's not the first message, move it to the top
        if system_msg_idx is not None:
            system_message = conversation.pop(system_msg_idx)
            conversation.insert(0, system_message)

def trim_conversation_to_fit_limit(conversation, token_limit, conversation_id):
    """Trim the earliest non-system messages until the conversation is within the token limit."""
    while count_tokens_in_conversation(conversation) > token_limit:
        # If the second message is not a system message, remove it.
        # This ensures the first message (system message) always remains.
        if conversation[1]["role"] != "system":
            conversation.pop(1)
        else:
            # If for some reason there are multiple system messages or the order is not as expected
            ensure_system_message_on_top(conversation)
            conversation.pop(2)
        
        store_conversation(conversation_id, conversation)

def store_conversation(conversation_id, conversation, is_busy=False):
    
    token_limit = 7000
    
    # Ensure the system message is always the first message in the conversation
    ensure_system_message_on_top(conversation)

    # Trim the conversation to fit within the token (or message) limit
    trim_conversation_to_fit_limit(conversation, token_limit, conversation_id)

    # Now, store the conversation in the database
    c = db_conn.cursor()
    values = (conversation_id, json.dumps(conversation), is_busy)
    c.execute("REPLACE INTO conversations VALUES (?, ?, ?)", values)
    db_conn.commit()
