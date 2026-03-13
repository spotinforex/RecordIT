import logging, os, asyncio
from logic.data_processing import complaint_processor, whatsapp_logger
from agent.ai import generate_response
from logic.message_handler import send_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def message_pipeline(data):
    '''
    Pipeline processor for incoming messages
    Args:
        data: incoming message in json format
    '''
    try:
        result = complaint_processor(data)
        if not result:
            logging.warning("complaint_processor returned None. Skipping pipeline.")
            return

        sender, message, timestamp = result

        ai_response = generate_response(sender, message)
        if not ai_response:
            logging.warning(f"No AI response generated for sender: {sender}")
            return

        if ai_response.get("CompleteInfo") == True:
            ai_response["Phone Number"] = sender
            status = await asyncio.to_thread(whatsapp_logger, ai_response)
            logging.info(f"Complaint logged for {sender}. Status: {status}")
            feedback = await send_message(sender, "Your complaint has been recorded and we will process it soon, Please be patient")

        elif ai_response.get("CompleteInfo") == False :
            logging.info("Sending message for more information")
            status = await send_message(sender, ai_response.get("Question"))
        else:
            logging.info(f"{ai_response.get("CompleteInfo")}")

    except Exception as e:
        logging.error(f"An Error In the Message Pipeline. Error: {e}")


