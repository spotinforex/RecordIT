from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from logic.debouncer_pipeline import debounce_pipeline
from logic.data_processing import complaint_processor
from logic.session import set_human_mode, is_human_mode, clear_human_mode
import logging, os, re, asyncio
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YOUR_NUMBER = os.getenv("YOUR_INSTANCE_WID")  # Whatsapp Number
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")  

app = FastAPI()
bearer_scheme = HTTPBearer(auto_error=False)

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    '''
    Green API sends: Authorization: Bearer <token>
    or              Authorization: Basic <token>
    HTTPBearer extracts the token from either automatically.
    '''
    if not credentials or credentials.credentials != WEBHOOK_TOKEN:
        logger.warning("Unauthorized webhook request — invalid or missing token.")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials

@app.post("/webhook")
async def webhook(request: Request, credentials: HTTPAuthorizationCredentials = Security(verify_token)):
    try:
        data = await request.json()
        logger.info(f"Incoming webhook: {data}")
        type_webhook = data.get("typeWebhook")

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

        if is_human_mode(str(sender)):
            logger.info(f"Human mode active for {sender} — AI suppressed.")
            return JSONResponse({"status": "human_mode"})

        asyncio.create_task(debounce_pipeline(str(sender), message, data))
        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

@app.get("/")
async def health_check():
    return {"status": "running", "service": "NGO Complaints Webhook"}

@app.post("/handback/{sender}")
async def handback(sender: str, credentials: HTTPAuthorizationCredentials = Security(verify_token)):
    clear_human_mode(sender)
    logger.info(f"AI restored for {sender}")
    return JSONResponse({"status": "ai_restored", "sender": sender})
