import anthropic
import os

async def generate_html(prompt):    
    print("STARTING PAGE GENERATION")
    client = anthropic.AsyncAnthropic(api_key=os.getenv("CLAUDE_API_KEY"))

    system_message = """
     Your task is to create a one-page website based on the given specifications, delivered as an HTML file with embedded JavaScript and CSS.  
     The HTML, CSS, and JavaScript code should be well-structured, efficiently organized, and properly commented for readability and maintainability. 
     The output should only be the code, DO NOT INCLUDE any text other than code. 
     Under NO circumstances should the response include the bracketed jinja tags, ONLY include the code that would replace the comment.

    Important instructions:
    1. The HTML should work with this format:
       {% extends "layout.html" %}
       {% block content %}
       <div class="container mx-auto">
       <!-- Your generated HTML, CSS, and JavaScript code goes here -->
       </div>
       {% endblock %}

    2. Only generate HTML, CSS, and JavaScript that fits within the content block, build it for mobile screens.
    3. Do not include {% extends "layout.html" %}
       {% block content %} and  {% endblock %} in your response.
    3. Avoid generating new style classes that are not essential. You have tailwindcss classes available.
    4. Do not include any <html>, <head>, or <body> tags.
    5. Include inline JavaScript within <script> tags inside the content block.
    6. Include CSS within a <style> tag inside the content block.
    7. Ensure all your code is self-contained within the content block.
    """

    try:
        message = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            temperature=0,
            system=system_message,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        raise Exception(f"Error generating content: {str(e)}")


    print("RESONSE RECIEVED")
    generated_html = message.content[0].text

    return generated_html
