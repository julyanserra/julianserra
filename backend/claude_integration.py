import os
from anthropic import Anthropic

class ClaudeAPI:

    def __init__(self):
        self.client = Anthropic(
        # This is the default and can be omitted
        api_key=os.environ.get("CLAUDE_API_KEY"),
        )
        self.model = "claude-3-5-sonnet-20240620"  # or whichever model you prefer


    def generate_response(self, user_message):
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error generating response from Claude: {str(e)}")
            return "I'm sorry, I'm having trouble responding right now."

    # Add more methods as needed for Claude API integration