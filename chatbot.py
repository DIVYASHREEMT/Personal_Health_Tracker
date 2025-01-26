import os
from creds import API_KEY
import google.generativeai as genai

# Configure the API with the new API key
genai.configure(api_key=API_KEY)

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def GenerateResponse(input_text):
    # Define a simple mapping of inputs to responses
    responses = {
        "hello": "Hello! How can I assist you today?",  # Updated response
        "hi": "Hello! What's on your mind?",
        "help": "Of course! I’m here to assist. Please let me know how I can be of service.",
        # Add more predefined responses as needed
    }

    # Normalize input to lowercase
    input_text = input_text.lower()

    # Check if the input matches any predefined responses
    if input_text in responses:
        return responses[input_text]

    # If no match, generate a response using the model
    response = model.generate_content([input_text])
    return response.text

while True:
    string = str(input("Enter your prompt: "))
    print("Bot: ", GenerateResponse(string))
