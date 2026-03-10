GREEN_API_INSTANCE_ID = os.getenv("GREEN_API_INSTANCE_ID")
GREEN_API_TOKEN       = os.getenv("GREEN_API_TOKEN")
GREEN_API_BASE_URL    = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE_ID}"

async def send_message(to: str, text: str):
    url = f"{GREEN_API_BASE_URL}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{to}@c.us",
        "message": text
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
    return response.json()

async def download_image(message_id: str, chat_id: str) -> bytes | None:
    url = f"{GREEN_API_BASE_URL}/downloadFile/{GREEN_API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "idMessage": message_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        # data["downloadUrl"] holds the actual file link
        file_url = data.get("downloadUrl")
        if file_url:
            async with httpx.AsyncClient() as client:
                file_response = await client.get(file_url)
                return file_response.content
    return None
