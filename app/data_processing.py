import pandas as pd
from app.db import DatabaseConnection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db = DatabaseConnection()

def whatsapp_receiver():
    '''Connect to the whatsapp websocket and receive messages
    Returns:
        json: A message received from the websocket in json format
    '''
    pass

def complaint_processor(message):
    '''Process a message received from the whatsapp websocket and extract relevant information
    Args:
        message (json): A message received from the whatsapp websocket in json format
    Returns:
        dict: A dictionary containing the extracted information
    '''
    pass