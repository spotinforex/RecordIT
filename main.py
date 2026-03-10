from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.connector import message_pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Incoming webhook: {data}")
        type_webhook = data.get("typeWebhook")

        # Only process incoming messages
        if type_webhook != "incomingMessageReceived":
            return JSONResponse({"status": "ignored"})
        message_pipeline(data)
        
        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

@app.get("/")
async def health_check():
    return {"status": "running", "service": "NGO Complaints Webhook"}
