import pandas as pd
from db import DatabaseConnection
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def complaint_processor(payload):
    '''
    Process a message received from the whatsapp websocket and extract relevant information
    Args:
        payload (json): A message received from the whatsapp websocket in json format
    Returns:
        sender: Unique phone number of sender
        text_message: Sender's message
        timestamp: Time message was sent 
    '''
    try:
        sender = payload.get("senderData", {}).get("sender")
        
        if sender is None:
            return None
            
        message = (
            payload.get("messageData", {})
            .get("textMessageData", {})
            .get("textMessage", "")
            .strip("{}'")
        )

        timestamp = payload.get("timestamp")
        date = datetime.fromtimestamp(timestamp)
        formatted = date.strftime("%Y-%m-%d %H:%M:%S")

        return sender, message, formatted
    
    except Exception as e:
        logging.error(f"Error Extracting Whatsapp Message: {e}")
        return None

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
        pass 
    except Exception as e:
        logging.error(f"Failed to Upload whatsapp complaint to database. Error: {e}")


