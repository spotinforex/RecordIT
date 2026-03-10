import logging, os
from data_processing import complaint_processor, whatsapp_logger
from ai import generate_response
from message_handler import send_message

logging.basicConfig(level = logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def message_pipeline(data):
    '''
    Pipeline processor for incoming messages
    Args:
        data: incoming message in json  format
    '''
    try:
        sender, message, timestamp  = complaint_processor(data)

        ai_response = generate_response(json_data)

        if ai_response.get("CompleteInfo") == True:
            status = whatsapp_logger(sender, timestamp, ai_response)
            if status is False:
                logging.info("Failed to upload complaint to the database")
                
        if ai_response.get("CompleteInfo") == False:
            status = send_message(to, ai_response)
            logging.info(f"Message Sent to {to}")
            
    except Exception as e:
        logging.error(f"An Error In the Message Pipeline. Error: {e}")
        
