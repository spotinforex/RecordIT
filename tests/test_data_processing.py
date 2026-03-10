if __name__ == "__main__":
    data = {'typeWebhook': 'incomingMessageReceived', 'instanceData': {'idInstance': 7107541949, 'wid': '2347078609112@c.us', 'typeInstance': 'whatsapp'}, 'timestamp': 1773129664, 'idMessage': 'ACD98C9249A02A89BDA00113E8543613', 'senderData': {'chatId': '2349168615642@c.us', 'chatName': 'Amarachi', 'sender': '2349168615642@c.us', 'senderName': 'Amarachi', 'senderContactName': ''}, 'messageData': {'typeMessage': 'textMessage', 'textMessageData': {'textMessage': 'Hello'}}}
    
    result = complaint_processor(data)
    print(result)
