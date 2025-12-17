# Competitor Research Application

A Django-based web application for researching and analyzing competitors. The application uses OpenAI to identify competitors for a given company and stores company data including funding, net worth, and user statistics.

## 🚀 Live Demo

The application is live and available at: **[http://13.126.87.126:8000/](http://13.126.87.126:8000/)**

Try it out by entering a company website URL to discover competitors and view market insights including net worth, user growth, and funding trends.

## Features

- **Competitor Discovery**: Find competitors for any company using AI-powered analysis
- **Company Data Management**: Store and track company information including:
  - Company details (name, website URL)
  - Funding records
  - Net worth records
  - User statistics
- **RESTful API**: API endpoint for programmatic access to competitor research
- **Streaming Responses**: Server-Sent Events (SSE) support for real-time updates
- **Flexible Database**: Supports both SQLite (development) and PostgreSQL via Supabase (production)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (Python 3.13 recommended)
- **pip** (Python package manager)
- **PostgreSQL** (optional, only if using Supabase/PostgreSQL database)
- **OpenAI API Key** (required for competitor analysis)
- **Supabase Account** (optional, for cloud database)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd competitor-research
```

### 2. Create a Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root directory:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# OpenAI Configuration (Required)
OPENAI_API_KEY=your-openai-api-key-here

# Supabase Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

**Note**: 
- The `SECRET_KEY` can be generated using Django's `python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- If `DATABASE_URL` is not provided, the application will use SQLite (default)
- `SUPABASE_URL` and `SUPABASE_KEY` are optional and only needed if you're using Supabase-specific features

### 5. Run Database Migrations

```bash
python manage.py migrate
```

This will create the necessary database tables. If using SQLite, a `db.sqlite3` file will be created in the project root.

### 6. Create a Superuser (Optional)

To access the Django admin interface:

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

## Running the Application

### Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Access Points

**Local Development:**
- **Home Page**: `http://localhost:8000/`
- **Admin Panel**: `http://localhost:8000/admin/`
- **API Endpoint**: `http://localhost:8000/api/competitors/`

**Live Production:**
- **Live Application**: [http://13.126.87.126:8000/](http://13.126.87.126:8000/)
- **API Endpoint**: `http://13.126.87.126:8000/api/competitors/`

### Production Deployment

For production deployment, use a production-ready WSGI server like Gunicorn:

```bash
gunicorn competitor_research.wsgi:application
```

See `DEPLOYMENT.md` for more detailed deployment instructions.

## Testing

### Running Django Tests

The project includes a test suite. Run tests using:

```bash
python manage.py test
```

To run tests for a specific app:

```bash
python manage.py test companies
```

### Manual API Testing

You can test the API endpoint using the provided test script:

1. Start the Django server in one terminal:
   ```bash
   python manage.py runserver
   ```

2. In another terminal, run the test script:
   ```bash
   python test_api.py
   ```

### API Testing with cURL

**POST Request:**
```bash
curl -X POST http://localhost:8000/api/competitors/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com"}'
```

**GET Request:**
```bash
curl "http://localhost:8000/api/competitors/?url=https://www.example.com"
```

### Testing with Python Requests

```python
import requests

url = "http://localhost:8000/api/competitors/"
response = requests.post(
    url,
    json={"url": "https://www.example.com"},
    headers={"Content-Type": "application/json"}
)
print(response.json())
```

## Project Structure

```
competitor-research/
├── companies/              # Main application
│   ├── migrations/        # Database migrations
│   ├── templates/         # HTML templates
│   ├── admin.py          # Django admin configuration
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   └── tests.py          # Unit tests
├── competitor_research/   # Project settings
│   ├── settings.py       # Django settings
│   ├── urls.py           # URL routing
│   ├── wsgi.py           # WSGI configuration
│   ├── openai_service.py # OpenAI integration
│   └── supabase_service.py # Supabase integration
├── staticfiles/          # Collected static files
├── db.sqlite3            # SQLite database (if used)
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
└── README.md             # This file
```

## API Documentation

### Find Competitors

**Endpoint**: `/api/competitors/`

**Methods**: `GET`, `POST`

**Description**: Finds competitors for a given company URL using AI analysis.

**Request Parameters**:
- `url` (string, required): The company website URL to analyze

**Request Examples**:

**POST Request:**
```json
{
  "url": "https://www.example.com"
}
```

**GET Request:**
```
GET /api/competitors/?url=https://www.example.com
```

**Response**: 
- Returns a streaming response with Server-Sent Events (SSE)
- Progress updates are sent as events
- Final result includes competitor information

**Error Responses**:
- `400 Bad Request`: Missing or invalid URL parameter
- `500 Internal Server Error`: Server-side error during processing

## Database Models

### Company
- `id`: UUID (Primary Key)
- `name`: Text field
- `website_url`: Text field (optional)
- `created_at`: DateTime
- `updated_at`: DateTime

### CompanyFunding
- `id`: UUID (Primary Key)
- `company`: Foreign Key to Company
- `value_usd`: Decimal
- `year`: Integer
- `source_url`: Text field
- `created_at`: DateTime

### CompanyNetworth
- `id`: UUID (Primary Key)
- `company`: Foreign Key to Company
- `value_usd`: Decimal
- `year`: Integer
- `source_url`: Text field
- `created_at`: DateTime

### CompanyUsers
- `id`: UUID (Primary Key)
- `company`: Foreign Key to Company
- `value`: BigInteger
- `year`: Integer
- `source_url`: Text field
- `created_at`: DateTime

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure your virtual environment is activated and all dependencies are installed.

2. **Database Connection Error**: 
   - Check your `DATABASE_URL` format if using PostgreSQL
   - Ensure PostgreSQL is running (if using local PostgreSQL)
   - Verify Supabase credentials if using Supabase

3. **OpenAI API Errors**:
   - Verify your `OPENAI_API_KEY` is correct and has sufficient credits
   - Check your OpenAI API usage limits

4. **Migration Errors**:
   - Try running `python manage.py makemigrations` first
   - Then run `python manage.py migrate`

5. **Static Files Not Loading**:
   - Run `python manage.py collectstatic` to collect static files
   - Ensure `STATIC_ROOT` is properly configured in settings

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Specify your license here]

## Support

For issues and questions, please open an issue on the repository.

