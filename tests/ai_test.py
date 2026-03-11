from app.ai import generate_response

if __name__ == "__main__":
    prompt = ["I have not recieved my payment", "yp/c4/3939", "my name is samuel daniel", "november 2025 and december 2025"]
    for i in prompt:
        response = generate_response("abc",i)
        print(f"Prompt: {i}\nResponse: {response}")
