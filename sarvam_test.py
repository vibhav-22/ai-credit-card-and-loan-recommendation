import os
import sys
from dotenv import load_dotenv
from sarvamai import SarvamAI

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    sys.exit("Error: SARVAM_API_KEY is not set in .env. Please add your key and try again.")

# Initialize client
client = SarvamAI(api_subscription_key=api_key)

# Make chat completion call
response = client.chat.completions(
    messages=[
        {"role": "user", "content": "Hello! Please introduce yourself in one short sentence."}
    ],
    model="sarvam-105b-conversations",
)

# Print the reply
print(response.choices[0].message.content)
