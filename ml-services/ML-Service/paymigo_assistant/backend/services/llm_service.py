import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("paymigo_assistant/.env")

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        self.base_url = "https://api.groq.com/openai/v1"
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat_completion(self, messages, tools=None, tool_choice="auto"):
        try:
            params = {
                "model": self.model,
                "messages": messages,
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice
                
            response = self.client.chat.completions.create(**params)
            return response
        except Exception as e:
            print(f"Error in Groq API call: {e}")
            return None

if __name__ == "__main__":
    # Test LLM connection
    service = LLMService()
    test_messages = [{"role": "user", "content": "Hello Migo!"}]
    res = service.chat_completion(test_messages)
    if res:
        print(f"Response: {res.choices[0].message.content}")
