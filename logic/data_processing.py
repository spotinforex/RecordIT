from logic.db import DatabaseConnection
import logging, re
from datetime import datetime
from utils.retry import retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def complaint_processor(payload):
    '''
    Process a message received from the whatsapp websocket and extract relevant information
    Args:
        payload (json): A message received from the whatsapp websocket in json format
    Returns:
        sender_number: Unique phone number of sender
        text_message: Sender's message
        timestamp: Time message was sent 
    '''
    try:
        sender = payload.get("senderData", {}).get("sender")
        
        if sender is None:
            return None
            
        if sender.endswith("@g.us"):
            logging.warning(f"Message from group chat ignored: {chat_id}")
            return None
            
        sender_number = int(re.search(r'(\d+)@', sender).group(1))
            
        message = (
            payload.get("messageData", {})
            .get("textMessageData", {})
            .get("textMessage", "")
            .strip("{}'")
        )

        timestamp = payload.get("timestamp")
        date = datetime.fromtimestamp(timestamp)
        formatted = date.strftime("%Y-%m-%d %H:%M:%S")

        return sender_number, message, formatted
    
    except Exception as e:
        logging.error(f"Error Extracting Whatsapp Message: {e}")
        return None

@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,))
def whatsapp_logger(data):
    '''
    Logs Whatsapp Complaints to the database
    Args:
        data: complaint data in json format
    Returns:
      status of upload
    '''
    try:
        db = DatabaseConnection()
        
        query = """
            INSERT INTO public.complaint (
                "Complainant Code",
                "Cohort",
                "Type of Complainant",
                "Complainant Name",
                "Complaint Category",
                "Communication Channel",
                "Complainant Feedback",
                "Phone Number"
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
        values = (
            data.get("ComplainantCode").upper(),
            data.get("Cohort"),
            data.get("TypeOfComplainant"),
            data.get("ComplainantName"),
            data.get("ComplaintCategory"),
            "WhatsApp",                         # hardcoded since this is the whatsapp logger
            data.get("ComplainantFeedback"),
            data.get("Phone Number")
        )
        status = db.execute_query(query, values)
        if status is False:
            logging.info(f"Failed to log WhatsApp complaint for: {data.get('ComplainantName')}")
            raise
            
        logging.info(f"WhatsApp complaint logged successfully for: {data.get('ComplainantName')}")
        return True

    except Exception as e:
        logging.error(f"Failed to Upload whatsapp complaint to database. Error: {e}")
        raise

