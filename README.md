# Personal Website with AI Voice Interaction

This project is a personal website with an integrated AI voice interaction feature. It uses Flask as the web framework, Supabase for database management, and integrates with various APIs including Speechify for text-to-speech, Braintrust for AI responses, and Stripe for payments.

## Features

- Personal information pages
- AI-powered chat interface with voice output
- Custom voice creation and management
- Quote management
- Golf score tracking and handicap calculation
- Admin interface for content management
- Stripe integration for payments

## Getting Started

### Prerequisites

- Python 3.7+
- pip
- Supabase account
- Stripe account
- Speechify API key
- Braintrust API key
- Cloudflare R2 account (for image storage)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-name>
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add the following variables:
   ```
   SUPABASE_URL=<your-supabase-url>
   SUPABASE_KEY=<your-supabase-key>
   SPEECHIFY_API_KEY=<your-speechify-api-key>
   BRAINTRUST_API_KEY=<your-braintrust-api-key>
   STRIPE_API_KEY=<your-stripe-api-key>
   CLOUDFLARE_PUBLIC_URL=<your-cloudflare-r2-public-url>
   SECRET_KEY=<your-flask-secret-key>
   ```

4. Initialize the database:
   Run the necessary SQL scripts to set up your Supabase tables (not provided in the given files).

### Running the Application

Run the Flask application:
```
python app.py
```

The application will be available at `http://localhost:5000`.

## Project Structure

```
.
├── app.py
├── backend/
│   ├── supabase_db.py
│   ├── speechify_integration.py
│   ├── braintrust_integration.py
│   ├── stripe_integration.py
│   ├── cloudflare_integration.py
│   ├── helpers.py
│   └── models.py
├── templates/
│   └── (HTML templates - not provided)
├── static/
│   └── (Static files - not provided)
└── requirements.txt
```

## Key Components

- `app.py`: Main Flask application
- `supabase_db.py`: Database operations using Supabase
- `speechify_integration.py`: Text-to-speech functionality
- `braintrust_integration.py`: AI chat responses
- `stripe_integration.py`: Payment processing
- `cloudflare_integration.py`: Image storage
- `models.py`: Data models and database operations

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Structure Diagram
```mermaid
graph TD
    A[app.py] --> B[Flask App]
    B --> C[Routes]
    B --> D[Templates]
    B --> E[Static Files]
    
    A --> F[backend/]
    F --> G[supabase_db.py]
    F --> H[speechify_integration.py]
    F --> I[braintrust_integration.py]
    F --> J[stripe_integration.py]
    F --> K[cloudflare_integration.py]
    F --> L[helpers.py]
    F --> M[models.py]
    
    G --> N[Supabase]
    H --> O[Speechify API]
    I --> P[Braintrust API]
    J --> Q[Stripe API]
    K --> R[Cloudflare R2]
    
    C --> S[Index]
    C --> T[Chat]
    C --> U[Admin]
    C --> V[Custom Voice]
    C --> W[Golf]
    
    M --> N
    ```