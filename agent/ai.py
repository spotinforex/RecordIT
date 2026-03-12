import requests
import logging, os, json, re
from dotenv import load_dotenv
from pathlib import Path
from logic.session import save_chat, get_chat_history
from utils.retry import retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

def read_system_instructions(file_path):
    '''Read system instructions from a file
    Args:  
        file_path (str): The path to the file containing system instructions
    Returns:
        str: The system instructions read from the file, or None if an error occurs
    '''
    try:
        path = Path.cwd() / file_path
        with open(rf"{path}", 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"Error reading system instructions from {file_path}: {e}")
        return None

@retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(requests.exceptions.RequestException,))
def generate_response(session_id, prompt):
    '''Generate a response from OpenRouter based on a user prompt
    Args:
        session_id (str): Unique session state identifier
        prompt (str): The user prompt to send to OpenRouter
    Returns:
        dict: Parsed JSON response from the AI, or None if an error occurs
    '''
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = read_system_instructions("agent/system_instructions/system_prompt.txt")
    history = get_chat_history(session_id)

    if history:
        full_prompt = f"{system_prompt}\n\nConversation History: {history}\n\nUser: {prompt}"
    else:
        full_prompt = f"{system_prompt}\n\nUser: {prompt}"

    data = {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [
            {"role": "user", "content": full_prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
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
        # Try raw JSON first
        try:
            parsed = json.loads(ai_response)
        except json.JSONDecodeError:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if not match:
                logging.warning(f"No JSON found in AI response: {ai_response}")
                return None
            try:
                parsed = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON block from AI response: {e}")
                return None

        question = parsed.get("Question")
        if question:
            conversation = f"User: {prompt}\n\nAI: {question}"
            save_chat(session_id, conversation)

        return parsed

    except requests.exceptions.RequestException as e:
        logging.error(f"OpenRouter API request failed: {e}")
        raise

