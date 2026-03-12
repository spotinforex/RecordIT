import logging, time, os, json
from dotenv import load_dotenv
import redis
from utils.retry import retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

def redis_connection():
    try:
        redis_url = os.getenv("REDIS_URL")
        redis_client = redis.Redis.from_url(
            redis_url,
            decode_responses=True
        )
        return redis_client
    except Exception as e:
        logging.error(f"Failed to connect to redis. Error: {e}")
        return None

def _ensure_list_key(redis_client, session):
    """
    Ensures the Redis key is a list type. Deletes it if it's the wrong type.
    """
    if redis_client.exists(session):
        key_type = redis_client.type(session)
        if key_type != 'list': 
            logging.warning(f"Redis key {session} is type '{key_type}', not a list. Deleting.")
            redis_client.delete(session)

@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(redis.RedisError, ConnectionError))
def save_chat(session_id, chat):
    """
    Saves chat conversation in Redis as a list.
    """
    try:
        redis_client = redis_connection()
        if redis_client:
            session = f"chat:{session_id}"
            _ensure_list_key(redis_client, session)
            redis_client.rpush(session, chat)
            logging.info(f"Conversation saved successfully")
            return True
        logging.warning(f"Failed to save conversation for session Id: {session_id}")
        raise
    except Exception as e:
        logging.error(f"Error when saving conversation history: {e}")
        raise

@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(redis.RedisError, ConnectionError))
def get_chat_history(session_id, last_n=5):
    """
    Retrieves last N messages from Redis chat history.
    """
    try:
        redis_client = redis_connection()
        if redis_client:
            session = f"chat:{session_id}"
            _ensure_list_key(redis_client, session)  # ← this was the missing fix
            conversation_history = redis_client.lrange(session, -last_n, -1)
            return conversation_history
        logging.warning(f"Failed to get conversation history for session Id: {session_id}")
        raise
    except Exception as e:
        logging.error(f"Error retrieving conversation history: {e}")
        raise

@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(redis.RedisError, ConnectionError))
def set_human_mode(sender: str, expires: int = 3600):
    redis_client = redis_connection()
    if not redis_client:
        raise ConnectionError("Failed to get Redis connection.")
    redis_client.setex(f"human_mode:{sender}", expires, "1")
    logging.info(f"Human mode activated for {sender}")


@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(redis.RedisError, ConnectionError))
def is_human_mode(sender: str) -> bool:
    redis_client = redis_connection()
    if not redis_client:
        raise ConnectionError("Failed to get Redis connection.")
    return redis_client.exists(f"human_mode:{sender}") == 1


@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(redis.RedisError, ConnectionError))
def clear_human_mode(sender: str):
    redis_client = redis_connection()
    if not redis_client:
        raise ConnectionError("Failed to get Redis connection.")
    redis_client.delete(f"human_mode:{sender}")
    logging.info(f"Human mode cleared for {sender}")

def is_duplicate(id_message: str) -> bool:
    try:
        redis_client = redis_connection()
        if not redis_client:
            return False
        key = f"seen:{id_message}"
        is_new = redis_client.set(key, 1, ex=1800, nx=True)
        return not is_new
    except Exception as e:
        logger.error(f"Duplicate check failed: {e}")
        return False
