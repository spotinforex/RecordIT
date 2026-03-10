import logging, time, os
from dotenv import load_dotenv
import redis 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def redis_connection():
    try:
        redis_url = os.getenv("REDIS_URL")
        redis_client  = redis.Redis.from_url(
            redis_url,
            decode_responses=True
        )
        return redis_client
    except Exception as e:
        logging.error(f"Failed to connect to redis. Error: {e}")
        return None

def save_chat(session_id, chat):
    '''
    Saves chat conversation on redis
    Args:
        session_id: Unique session identifier
        chat: Conversation with llm
    Returns:
        True when successful else None
    '''
    try:
        redis = redis_connection()
        if redis:
            session = f"chat:{session_id}"
            redis.set(session, chat)
            return true
        logging.warning(f"Failed to save Conversation for session Id: {session}")
        return None
    except Exception as e:
        loggging.error(f"An Error when saving conversation history. Error: {e}")
        return None

def get_chat_history(session_id):
    '''
    Retreives Past Conversations
    Args:
        session_id: Unique session identifier
    Returns:
        Conversation History when successful else None
    '''
    try:
        redis = redis_connection()
        if redis:
            session = f"chat:{session_id}"
            conversation_history = redis.lrange(session, 0, 5)  # Last five conversations
            return conversation_history
        logging.warning(f"Failed to get conversation history for session Id: {session}")
        return None
    except Exception as e:
        loggging.error(f"An Error when saving conversation history. Error: {e}")
        return None
