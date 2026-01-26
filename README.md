# Survey API - FastAPI Backend

A comprehensive survey management API built with FastAPI, SQLAlchemy, and PostgreSQL/SQLite.

## Features

- ✅ User can create multiple surveys
- ✅ Users can fill surveys created by other users
- ✅ Image upload support for surveys
- ✅ JWT authentication with Clerk
- ✅ Survey response tracking and analytics
- ✅ RESTful API with comprehensive error handling
- ✅ CORS enabled for frontend integration

## Project Structure

```
survey-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration settings
│   ├── database.py            # Database connection and session
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── auth.py                # JWT authentication utilities
│   ├── file_upload.py         # File upload utilities
│   ├── routes/
│   │   ├── surveys.py         # Survey CRUD endpoints
│   │   └── responses.py       # Survey response endpoints
│   └── uploads/               # Directory for uploaded images
├── seed_db.py                 # Database seeding script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
└── README.md
```

## Installation

1. **Clone and setup virtual environment:**

```bash
cd survey-api
python -m venv venv
.\venv\Scripts\Activate.ps1  # On Windows
source venv/bin/activate      # On macOS/Linux
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Setup environment variables:**

```bash
# Edit .env file with your Clerk credentials
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
DATABASE_URL=sqlite:///./survey.db
FRONTEND_URL=http://localhost:3000
```

4. **Initialize database and seed data:**

```bash
python seed_db.py
```

5. **Run the server:**

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

## API Endpoints

### Surveys

- `GET /api/surveys` - List all active surveys
- `POST /api/surveys` - Create a new survey (requires auth)
- `GET /api/surveys/{survey_id}` - Get survey details
- `PUT /api/surveys/{survey_id}` - Update survey (owner only)
- `DELETE /api/surveys/{survey_id}` - Delete survey (owner only)
- `GET /api/surveys/my-surveys` - Get user's surveys (requires auth)

### Survey Images

- `POST /api/surveys/{survey_id}/upload-image` - Upload image to survey (owner only)
- `GET /api/surveys/{survey_id}/images` - Get survey images
- `DELETE /api/surveys/{survey_id}/images/{image_id}` - Delete image (owner only)

### Survey Responses

- `POST /api/surveys/{survey_id}/responses` - Submit survey response (requires auth)
- `GET /api/surveys/responses` - Get user's responses (requires auth)
- `GET /api/surveys/{survey_id}/responses` - Get all responses for survey (owner only)
- `GET /api/surveys/{survey_id}/results` - Get survey statistics and results
- `DELETE /api/surveys/responses/{response_id}` - Delete response (owner only)

## Authentication

The API uses Clerk JWT tokens for authentication. Include the Bearer token in the Authorization header:

```bash
Authorization: Bearer <your_clerk_jwt_token>
```

## Database Models

### Survey

- id (UUID)
- title (String)
- description (Text)
- created_by (User ID)
- created_at (DateTime)
- updated_at (DateTime)
- status (draft, active, closed)
- questions (Relationship)
- responses (Relationship)
- images (Relationship)

### Question

- id (UUID)
- survey_id (FK)
- type (text, multiple_choice, rating, checkbox)
- title (String)
- description (Text)
- required (Boolean)
- order (Integer)
- placeholder (String)
- min_value, max_value (for rating)

### Option

- id (UUID)
- question_id (FK)
- label (String)
- value (String)
- order (Integer)

### SurveyResponse

- id (UUID)
- survey_id (FK)
- user_id (String)
- responses (JSON - {question_id: answer})
- submitted_at (DateTime)

### SurveyImage

- id (UUID)
- survey_id (FK)
- filename (String)
- file_path (String)
- file_size (Integer)
- mime_type (String)
- uploaded_at (DateTime)

## Example Requests

### Create Survey

```bash
curl -X POST http://localhost:8000/api/surveys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Customer Feedback",
    "description": "Help us improve",
    "status": "active",
    "questions": [
      {
        "type": "text",
        "title": "What do you think?",
        "required": true,
        "order": 1,
        "options": []
      }
    ]
  }'
```

### Submit Response

```bash
curl -X POST http://localhost:8000/api/surveys/{survey_id}/responses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "responses": {
      "question_id_1": "answer_1",
      "question_id_2": ["option_1", "option_2"]
    }
  }'
```

### Upload Image

```bash
curl -X POST http://localhost:8000/api/surveys/{survey_id}/upload-image \
  -H "Authorization: Bearer <token>" \
  -F "file=@image.jpg"
```

## Environment Configuration

### .env file settings:

```
# Clerk
CLERK_SECRET_KEY=sk_test_xxxxx
CLERK_PUBLISHABLE_KEY=pk_test_xxxxx

# Database
DATABASE_URL=sqlite:///./survey.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/survey_db

# Server
DEBUG=True
LOG_LEVEL=INFO

# File Upload
MAX_UPLOAD_SIZE_MB=5
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/gif,image/webp

# CORS
FRONTEND_URL=http://localhost:3000
```

## Error Handling

All errors return a standardized format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400
}
```

## Development

To enable auto-reload during development:

```bash
python -m uvicorn app.main:app --reload
```

To run without debug mode:

```bash
python -m uvicorn app.main:app
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Use PostgreSQL instead of SQLite
3. Update `FRONTEND_URL` to production domain
4. Configure proper CORS settings
5. Use a production ASGI server (e.g., Gunicorn with Uvicorn workers)

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## License

MIT License
