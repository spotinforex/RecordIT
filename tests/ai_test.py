from app.ai import generate_response

if __name__ == "__main__":
    prompt = "What is the capital of France?"
    response = generate_response(prompt)
    print(f"Prompt: {prompt}\nResponse: {response}")