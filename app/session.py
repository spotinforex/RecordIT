import logging, time
from db import DatabaseConnection
from config import END_KEYWORD, SESSION_TIMEOUT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#db = DatabaseConnection()   Using db connection in session.py is optional for now and can be done when needed for database operations.

# Global sessions dictionary
sessions = {}

def finalize_session(sender_session: dict):
    """Finalize a session and return JSON-compatible dict"""
    sender_id = sender_session.get("sender_id")
    messages = sender_session.get("messages", [])

    logging.info(f"Finalizing session for sender_id: {sender_id}")

    # Mark session as complete
    sender_session["status"] = "complete"

    # Optionally remove from sessions to free memory
    sessions.pop(sender_id, None)

    return {"sender_id": sender_id, "messages": messages}


def handling_session(sender_id, message_text):
    """Handle incoming message, update session, and finalize if needed"""
    current_time = time.time()
    
    # Initialize session if not exists
    if sender_id not in sessions:
        sessions[sender_id] = {
            "sender_id": sender_id,
            "messages": [],
            "last_update": current_time,
            "status": "in_progress"
        }
    
    session = sessions[sender_id]
    
    # Append message
    session["messages"].append(message_text)
    session["last_update"] = current_time

    # Check if user sent the END keyword
    if message_text.strip().upper() == END_KEYWORD:
        return finalize_session(session)
    
    # Session timeout check (this should be handled by a background task in production)
    if current_time - session["last_update"]> SESSION_TIMEOUT:
        return finalize_session(session)
    
    # Session still in progress
    return {
        "sender_id": sender_id,
        "status": "in_progress",
        "messages_so_far": session["messages"]
    }


if __name__ == "__main__":
    # Example usage
    sender_id = "user123"
    messages = ["Hello", "I have a complaint about my order."]

    for msg in messages:
        result = handling_session(sender_id, msg)
        logging.info(f"Session result: {result}")