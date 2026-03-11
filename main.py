from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.debouncer_pipeline import debounce_pipeline
from app.data_processing import complaint_processor
from app.session import set_human_mode, is_human_mode, clear_human_mode
import logging, os, re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YOUR_NUMBER = os.getenv("YOUR_INSTANCE_WID")  # Whatsapp line

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Incoming webhook: {data}")
        type_webhook = data.get("typeWebhook")

        # Detect human agent replying outbound
        if type_webhook == "outgoingMessageReceived":
            sender_wid = data.get("senderData", {}).get("sender", "")
            chat_id = data.get("senderData", {}).get("chatId", "")
            if sender_wid == YOUR_NUMBER and chat_id.endswith("@c.us"):
                match = re.search(r'(\d+)@', chat_id)
                if match:
                    set_human_mode(match.group(1))
                    logger.info(f"Human mode activated for {match.group(1)}")
            return JSONResponse({"status": "human_reply_noted"})

        if type_webhook != "incomingMessageReceived":
            return JSONResponse({"status": "ignored"})

        result = complaint_processor(data)
        if not result:
            logger.warning("complaint_processor returned None. Skipping pipeline.")
            return JSONResponse({"status": "ignored"})

        sender, message, timestamp = result

        # Suppress AI if human has taken over
        if is_human_mode(str(sender)):
            logger.info(f"Human mode active for {sender} — AI suppressed.")
            return JSONResponse({"status": "human_mode"})

        # don't await the debounce task, return immediately
        asyncio.create_task(debounce_pipeline(str(sender), message, data))

        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@app.get("/")
async def health_check():
    return {"status": "running", "service": "NGO Complaints Webhook"}

