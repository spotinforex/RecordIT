from fastapi import FastAPI, Request, HTTPException, Security, WebSocketDisconnect, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from logic.debouncer_pipeline import debounce_pipeline
from logic.data_processing import complaint_processor
from logic.session import set_human_mode, is_human_mode, clear_human_mode, is_duplicate
from logic.websocket import manager
from db_retrieval.complaint_retrieval import single_complaint_retriever, multiple_complaint_retriever, PERIOD_MAP, complaints_to_excel
import logging, os, re, asyncio
from dotenv import load_dotenv
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YOUR_NUMBER = os.getenv("YOUR_INSTANCE_WID")  # Whatsapp Number
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")  

app = FastAPI()
bearer_scheme = HTTPBearer(auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://record-i-tfrontend.vercel.app",
        "http://localhost:3000",
    ],  
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/complaints/export")
async def export_complaints(
    period: str = None,
    credentials: HTTPAuthorizationCredentials = Security(verify_token)
):
    try:
        buffer = complaints_to_excel(period)
        if buffer is None:
            return JSONResponse(
                {"error": f"Invalid period. Choose from: {list(PERIOD_MAP.keys())}"},
                status_code=400
            )

        # filename includes period and date for easy identification
        label = period or "all"
        filename = f"complaints_{label}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Failed to export complaints: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/complaints/{complaint_id}")
async def get_complaint(complaint_id: str, credentials: HTTPAuthorizationCredentials = Security(verify_token)):
    try:
        complaint = single_complaint_retriever(complaint_id)
        if complaint is None:
            return JSONResponse({"error": "Complaint not found"}, status_code=404)
        return JSONResponse({"complaint": complaint})
    except Exception as e:
        logger.error(f"Failed to fetch complaint {complaint_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/complaints")
async def get_complaints(
    period: str = None,
    credentials: HTTPAuthorizationCredentials = Security(verify_token)
):
    try:
        complaints = multiple_complaint_retriever(period)
        if complaints is None:
            return JSONResponse(
                {"error": f"Invalid period. Choose from: {list(PERIOD_MAP.keys())}"},
                status_code=400
            )
        
        return JSONResponse({
            "complaints": complaints,
            "count": len(complaints),
            "period": period or "all"
        })
    except Exception as e:
        logger.error(f"Failed to fetch complaints: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
        
@app.post("/webhook")
async def webhook(request: Request, credentials: HTTPAuthorizationCredentials = Security(verify_token)):
    try:
        data = await request.json()
        logger.info(f"Incoming webhook: {data}")
        type_webhook = data.get("typeWebhook")

        # Checks duplicate data  
        id_message = data.get("idMessage")
        if id_message and is_duplicate(id_message):
            logger.info(f"Duplicate webhook ignored: {id_message}")
            return JSONResponse({"status": "duplicate"}, status_code=200)

        if type_webhook == "outgoingMessageReceived":
            sender_wid = data.get("senderData", {}).get("sender", "")
            chat_id = data.get("senderData", {}).get("chatId", "")
            if sender_wid == YOUR_NUMBER and chat_id.endswith("@c.us"):
                match = re.search(r'(\d+)@', chat_id)
                if match:
                    set_human_mode(match.group(1))
                    logger.info(f"Human mode activated for {match.group(1)}")
            return JSONResponse({"status": "human_reply_noted"}, status_code=200)

        if type_webhook != "incomingMessageReceived":
            return JSONResponse({"status": "ignored"}, status_code=200)

        result = complaint_processor(data)
        if not result:
            logger.warning("complaint_processor returned None. Skipping pipeline.")
            return JSONResponse({"status": "ignored"}, status_code=200)

        sender, message, timestamp = result

        # Broadcast Message
        await manager.broadcast({
            "event": "new_message",
            "sender": str(sender),
            "message": message,
            "timestamp": timestamp
        })

        if is_human_mode(str(sender)):
            logger.info(f"Human mode active for {sender} — AI suppressed.")
            return JSONResponse({"status": "human_mode"}, status_code=200)

        task = asyncio.create_task(debounce_pipeline(str(sender), message, data))
        task.add_done_callback(
            lambda t: logger.error(f"debounce_pipeline failed: {t.exception()}") if t.exception() else None
        )
        return JSONResponse({"status": "ok"}, status_code=200)

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

@app.get("/")
async def health_check():
    return JSONResponse({"status": "running", "service": "NGO Complaints Webhook"}, status_code = 200)

@app.post("/handback/{sender}")
async def handback(sender: str, credentials: HTTPAuthorizationCredentials = Security(verify_token)):
    clear_human_mode(sender)
    logger.info(f"AI restored for {sender}")
    return JSONResponse({"status": "ai_restored", "sender": sender})
