import logging
import asyncio
from logic.data_processing import complaint_processor
from logic.debouncer_pipeline import debounce_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test():
    try:
        data = {'typeWebhook': 'incomingMessageReceived', 'instanceData': {'idInstance': 7107541949, 'wid': '2347078609112@c.us', 'typeInstance': 'whatsapp'}, 'timestamp': 1773129664, 'idMessage': 'ACD98C9249A02A89BDA00113E8543613', 'senderData': {'chatId': '2348146072877@c.us', 'chatName': 'Amarachi', 'sender': '2348146072877@c.us', 'senderName': 'Amarachi', 'senderContactName': ''}, 'messageData': {'typeMessage': 'textMessage', 'textMessageData': {'textMessage': 'Hello'}}}

        result = complaint_processor(data)
        if not result:
            logger.warning("complaint_processor returned None. Skipping pipeline.")
            return

        sender, message, timestamp = result
        await debounce_pipeline(sender, message, data)

        # ✅ Wait for all background tasks (the debounce flush) to complete
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if pending:
            logger.info(f"Waiting for {len(pending)} background task(s) to complete...")
            await asyncio.gather(*pending)

    except Exception as e:
        logger.error(f"Test error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
