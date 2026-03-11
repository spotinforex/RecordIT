if __name__ == "__main__":
    import time
    start = time.time()
    data = {'typeWebhook': 'incomingMessageReceived', 'instanceData': {'idInstance': 7107541949, 'wid': '2347078609112@c.us', 'typeInstance': 'whatsapp'}, 'timestamp': 1773129664, 'idMessage': 'ACD98C9249A02A89BDA00113E8543613', 'senderData': {'chatId': '2348146072877@c.us', 'chatName': 'Amarachi', 'sender': '2348146072877@c.us', 'senderName': 'Amarachi', 'senderContactName': ''}, 'messageData': {'typeMessage': 'textMessage', 'textMessageData': {'textMessage': 'Hello'}}}
    asyncio.run(message_pipeline(data))
    end = time.time()
    logging.info(f"Time Taken {end - start:2f} seconds")
