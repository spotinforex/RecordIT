import asyncio
import logging
from logic.session import redis_connection
from logic.connector import message_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEBOUNCE_SECONDS = 10
BUFFER_KEY = "debounce:buffer:{}"
TASK_REGISTRY = {}

async def debounce_pipeline(sender: str, message: str, data: dict):
    """
    Buffer incoming messages per sender. If a new message arrives within
    DEBOUNCE_SECONDS, reset the timer. Once timer expires, merge all buffered
    messages and send to pipeline as one.
    """
    redis_client = redis_connection()

    if not redis_client:
        logging.error(f"Redis unavailable. Dropping message from {sender}.")
        return

    buffer_key = BUFFER_KEY.format(sender)
    redis_client.rpush(buffer_key, message)
    redis_client.expire(buffer_key, DEBOUNCE_SECONDS + 5)

    if sender in TASK_REGISTRY:
        TASK_REGISTRY[sender].cancel()
        logging.info(f"Debounce timer reset for {sender}")

    task = asyncio.create_task(_flush_after_delay(sender, data, redis_client, buffer_key))
    TASK_REGISTRY[sender] = task


async def _flush_after_delay(sender: str, data: dict, redis_client, buffer_key: str):
    """
    Wait for DEBOUNCE_SECONDS, then merge buffered messages and fire the pipeline.
    """
    try:
        await asyncio.sleep(DEBOUNCE_SECONDS)

        buffered = redis_client.lrange(buffer_key, 0, -1)
        if not buffered:
            logging.warning(f"Buffer empty on flush for {sender}. Nothing to process.")
            return

        merged_message = " ".join(buffered)
        logging.info(f"Flushing {len(buffered)} buffered message(s) for {sender}: '{merged_message}'")

        redis_client.delete(buffer_key)
        TASK_REGISTRY.pop(sender, None)

        # ✅ Fixed: deepcopy data to avoid mutating the original webhook payload
        import copy
        flushed_data = copy.deepcopy(data)
        flushed_data["messageData"]["textMessageData"]["textMessage"] = merged_message
        await message_pipeline(flushed_data)

    except asyncio.CancelledError:
        # Expected — timer was reset by a new message, do nothing
        pass
    except Exception as e:
        logging.error(f"Error flushing debounce buffer for {sender}: {e}")
        # ✅ Clean up registry on unexpected failure so sender isn't stuck
        TASK_REGISTRY.pop(sender, None)
