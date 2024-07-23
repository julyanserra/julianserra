import os
from openai import OpenAI
import backend.helpers as helpers

#mini
open_ai = "gpt-4o-mini"
mistral = "mistral-large"
anthropic = "claude-3-5-sonnet-20240620"
google = "gemini-pro"

class BraintrustAPI:

    def __init__(self):
        self.client = OpenAI(
            base_url="https://braintrustproxy.com/v1",
            api_key=os.environ.get("BRAINTRUST_API_KEY") # Can use Braintrust, Anthropic, etc. API keys here
        )
        self.model = open_ai # or whichever model you prefer
        #set up message history
        #message history is a dictionary with a user and system messages
        self.message_history = {}
        

    def generate_response(self, visitor, user_message, prompt=None):
        #if user is not in message history, add them, with the context prompt
        user = visitor['fingerprint']
        if user not in self.message_history:
            self.message_history[user] = [{"role": "system", "content": helpers.processContext(visitor, prompt)}]
        try:
            #append user message to message history
            self.message_history[user].append({"role": "user", "content": user_message})
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.message_history[user],
                #set higher temperature for creativity
                temperature=0.7
            )
            response = response.choices[0].message.content
            
            self.message_history[user].append({"role": "assistant", "content": response})
            return response
        except Exception as e:
            print(f"Error generating response from Braintrust: {str(e)}")
            return "I'm sorry, I'm having trouble responding right now."


