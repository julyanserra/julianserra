# Virtual Curriculum Backend

This is the backend for the Virtual Curriculum application, which allows users to interact with a virtual version of the curriculum creator using Claude AI and Speechify for text-to-speech conversion.

## Setup

1. Ensure you have Python 3.8+ installed on your system.

2. Clone this repository and navigate to the backend directory:
   ```
   cd virtual_curriculum/backend
   ```

3. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Copy the `.env.example` file to `.env` and fill in your actual API keys and configuration values:
   ```
   cp .env.example .env
   ```

6. Edit the `.env` file with your actual Supabase, Speechify, and Claude API credentials.

## Running the Application

To run the backend server:

```
python app.py
```

The server will start running on `http://localhost:5000`.

## API Endpoints

- GET `/`: Welcome message
- GET `/curriculum`: Fetch the curriculum data
- POST `/chat`: Send a message to Claude AI and get a response
- POST `/text-to-speech`: Convert text to speech using Speechify

## Adding New Features

To add new features or modify existing ones:

1. Update the relevant integration file (`supabase_db.py`, `speechify_integration.py`, or `claude_integration.py`).
2. Modify `app.py` to add new routes or update existing ones.
3. Update this README if you've added new endpoints or changed the setup process.

## Troubleshooting

If you encounter any issues:

1. Ensure all environment variables are correctly set in your `.env` file.
2. Check that you've installed all required dependencies.
3. Make sure your API keys for Supabase, Speechify, and Claude are valid and have the necessary permissions.

For any other issues, please contact the project maintainer.