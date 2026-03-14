import requests
import logging, os, json, re
from dotenv import load_dotenv
from pathlib import Path
from logic.session import save_chat, get_chat_history
from utils.retry import retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")



def read_system_instructions(file_path: str) -> str | None:
    """Read system instructions from a text file.

    Args:
        file_path: Path relative to cwd for the system prompt file.
    Returns:
        File contents as a string, or None on error.
    """
    try:
        path = Path.cwd() / file_path
        return path.read_text(encoding='utf-8').strip()
    except Exception as e:
        logging.error(f"Error reading system instructions from {file_path}: {e}")
        return None


def extract_json(raw: str) -> dict | None:
    """Robustly extract and parse a JSON object from an AI response.

    Handles:
    - Raw JSON with no fences
    - ```json ... ``` fenced blocks
    - ``` ... ``` fenced blocks (no language tag)
    - Python literals: True/False/None → true/false/null

    Args:
        raw: Raw string content from the AI response.
    Returns:
        Parsed dict, or None if parsing fails.
    """
    text = raw.strip()

    # Strip code fences (with or without language tag)
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    # Fix Python literals that the model sometimes outputs
    text = text.replace('True', 'true').replace('False', 'false').replace('None', 'null')

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON after cleaning: {e}\nCleaned text: {text}")
        return None

@retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(requests.exceptions.RequestException,))
def generate_response(session_id: str, prompt: str) -> dict | None:
    """Generate a response from OpenRouter based on a user prompt.

    Args:
        session_id: Unique session state identifier.
        prompt: The user message to send to the AI.
    Returns:
        Parsed JSON dict from the AI response, or None on failure.
    """
    if not api_key:
        logging.error("OPENROUTER_API_KEY is not set.")
        return None

    system_prompt = read_system_instructions("agent/system_instructions/system_prompt.txt")
    if not system_prompt:
        logging.error("System prompt could not be loaded. Aborting.")
        return None

    history = get_chat_history(session_id)
    full_prompt = (
        f"Conversation History:\n{history}\n\nUser: {prompt}"
        if history
        else f"User: {prompt}"
    )

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [    
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_prompt}  
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        logging.info(f"OpenRouter status: {response.status_code}")
        response.raise_for_status()

        result = response.json()
        choices = result.get("choices", [])
        if not choices:
            logging.warning("No choices returned from OpenRouter.")
            return None

        ai_response = choices[0].get("message", {}).get("content", "").strip()
        if not ai_response:
            logging.warning("Empty response content from OpenRouter.")
            return None

        logging.info(f"Raw AI response: {ai_response}")

        parsed = extract_json(ai_response)
        if parsed is None:
            # llm not following instructions
            logging.warning(f"Could not parse JSON from AI response: {ai_response}")
            parsed = {"CompleteInfo": False, 
                       "Question": ai_response
                       }
            save_chat(session_id, f"User: {prompt}\n\nAI: {ai_response}")
            return parsed

        # Persist question turn to chat history
        question = parsed.get("Question")
        if question:
            save_chat(session_id, f"User: {prompt}\n\nAI: {question}")

        return parsed

    except requests.exceptions.RequestException as e:
        logging.error(f"OpenRouter API request failed: {e}")
        raise
