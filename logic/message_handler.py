import httpx
from dotenv import load_dotenv
import os, logging
from utils.retry import retry


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

GREEN_API_INSTANCE_ID = os.getenv("GREEN_API_INSTANCE_ID")
GREEN_API_TOKEN       = os.getenv("GREEN_API_TOKEN")
GREEN_API_BASE_URL    = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE_ID}"

@retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(httpx.HTTPError,httpx.ConnectError))
async def send_message(to: str, text: str):
    try:
        url = f"{GREEN_API_BASE_URL}/sendMessage/{GREEN_API_TOKEN}"
        payload = {
            "chatId": f"{to}@c.us",
            "message": text
        }
        # ✅ Fixed: async with + await on the post call
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)

        logging.info(f"Green API status: {response.status_code}")
        logging.info(f"Green API response: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error sending to {to}: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.HTTPError as e:
        logging.error(f"Failed to send message to: {to}. Error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error sending to {to}: {type(e).__name__}: {e}")
        raise


'''async def download_image(message_id: str, chat_id: str) -> bytes | None:
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
'''
