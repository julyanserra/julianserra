import anthropic
import os

def generate_html(prompt):
    client = anthropic.Anthropic(
        api_key=os.getenv('CLAUDE_API_KEY')
    )

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

    2. Only generate HTML, CSS, and JavaScript that fits within the content block.
    3. Avoid generating new style classes that are not essential. You have tailwindcss classes available.
    4. Do not include any <html>, <head>, or <body> tags.
    5. Include inline JavaScript within <script> tags inside the content block.
    6. Include CSS within a <style> tag inside the content block.
    7. Ensure all your code is self-contained within the content block.
    """

    message = client.messages.create(
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

    generated_html = message.content[0].text.strip()

    # Ensure the generated HTML starts and ends with the correct template tags
    if not generated_html.startswith('{% extends "layout.html" %}'):
        generated_html = '{% extends "layout.html" %}\n\n{% block content %}\n<div class="container mx-auto">\n' + generated_html
    if not generated_html.endswith('{% endblock %}'):
        generated_html += '\n</div>\n{% endblock %}'

    return generated_html