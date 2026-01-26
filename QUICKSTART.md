# FastAPI Survey Backend - Quick Start Guide

## ✅ Backend Implementation Complete!

Your FastAPI backend is ready with all features:

- ✅ User survey creation (multiple surveys per user)
- ✅ Multi-user survey participation
- ✅ Image upload support
- ✅ Clerk JWT authentication
- ✅ Survey response tracking & analytics
- ✅ RESTful API with error handling
- ✅ CORS enabled for Next.js frontend

## 📁 Project Structure

```
survey-api/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings & environment config
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # Clerk JWT authentication
│   ├── file_upload.py       # Image upload utilities
│   ├── routes/
│   │   ├── surveys.py       # Survey CRUD & image endpoints
│   │   └── responses.py     # Survey response submission & analytics
│   └── uploads/             # Uploaded images storage
├── seed_db.py               # Sample data initialization
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
└── README.md                # Full documentation
```

## 🚀 Getting Started

### Option 1: Automated Setup (Windows)

```bash
cd C:\MyWork\Research\survey-api
.\run.bat
```

### Option 2: Automated Setup (macOS/Linux)

```bash
cd ~/MyWork/Research/survey-api
chmod +x run.sh
./run.sh
```

### Option 3: Manual Setup

```bash
# 1. Navigate to project
cd C:\MyWork\Research\survey-api

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database with sample data
python seed_db.py

# 5. Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 What Gets Created

When you run the startup script:

1. ✅ Virtual environment setup
2. ✅ Dependencies installed
3. ✅ SQLite database created (`survey.db`)
4. ✅ 3 sample surveys seeded with demo data
5. ✅ FastAPI server running on http://localhost:8000

### Sample Data Includes:

- **Survey 1**: "Customer Satisfaction Survey" (by demo_user_1)
  - Multiple choice question
  - Rating scale (1-5)
  - Open text question

- **Survey 2**: "What features would you like?" (by demo_user_2)
  - Checkbox selection (multiple answers)
  - Open text feedback

- **Survey 3**: "User Experience Feedback" (by demo_user_1)
  - Rating scale (1-10)
  - Multiple choice (how you heard about us)

## 🔌 API Endpoints

### Public Endpoints (No Auth Required)

- `GET /` - Health check
- `GET /health` - Health status
- `GET /api/surveys` - List all active/closed surveys
- `GET /api/surveys/{id}` - Get survey details
- `GET /api/surveys/{id}/results` - Get survey statistics
- `GET /api/surveys/{id}/images` - Get survey images

### Protected Endpoints (Requires Clerk JWT)

- `POST /api/surveys` - Create survey
- `PUT /api/surveys/{id}` - Update survey (owner only)
- `DELETE /api/surveys/{id}` - Delete survey (owner only)
- `GET /api/surveys/my-surveys` - Get your surveys
- `POST /api/surveys/{id}/upload-image` - Upload image (owner only)
- `POST /api/surveys/{id}/responses` - Submit response
- `GET /api/surveys/responses` - Get your responses
- `GET /api/surveys/{id}/responses` - Get all responses (owner only)
- `DELETE /api/surveys/responses/{id}` - Delete response (owner only)

## 🔐 Environment Configuration

Edit `.env` file with your settings:

```env
# Clerk Authentication
CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key

# Database
DATABASE_URL=sqlite:///./survey.db
# For PostgreSQL: postgresql://user:password@localhost/survey_db

# Server
DEBUG=True
LOG_LEVEL=INFO

# File Upload
MAX_UPLOAD_SIZE_MB=5
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/gif,image/webp

# Frontend CORS
FRONTEND_URL=http://localhost:3000
```

## 📚 API Documentation

Once running, visit:

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Base**: http://localhost:8000/api

## 🔌 Connecting Frontend to Backend

Your Next.js frontend is already configured to connect to this backend!

In the frontend's `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

The frontend will automatically:

- Fetch surveys from `GET /api/surveys`
- Submit responses to `POST /api/surveys/{id}/responses`
- Include Clerk JWT tokens in Authorization headers

## 📤 Image Upload Example

```bash
curl -X POST http://localhost:8000/api/surveys/survey_id/upload-image \
  -H "Authorization: Bearer <clerk_token>" \
  -F "file=@path/to/image.jpg"
```

Images are stored in: `app/uploads/{survey_id}/`
Accessible at: `http://localhost:8000/uploads/{survey_id}/{filename}`

## 🗂️ Database Schema

### Surveys Table

- `id` - UUID primary key
- `title` - Survey title
- `description` - Survey description
- `created_by` - Creator's Clerk user ID
- `created_at` - Creation timestamp
- `status` - draft/active/closed
- Relationships: questions, responses, images

### Questions Table

- `id` - UUID primary key
- `survey_id` - FK to surveys
- `type` - text/multiple_choice/rating/checkbox
- `title` - Question text
- `required` - Is answer required?
- `order` - Display order
- Relationships: options

### Options Table

- `id` - UUID primary key
- `question_id` - FK to questions
- `label` - Display text
- `value` - Actual value
- `order` - Display order

### Responses Table

- `id` - UUID primary key
- `survey_id` - FK to surveys
- `user_id` - Respondent's Clerk user ID
- `responses` - JSON {question_id: answer}
- `submitted_at` - Submission timestamp

### Images Table

- `id` - UUID primary key
- `survey_id` - FK to surveys
- `filename` - Original filename
- `file_path` - Saved file path
- `file_size` - Size in bytes
- `mime_type` - Image MIME type
- `uploaded_at` - Upload timestamp

## 🐛 Troubleshooting

### Port 8000 Already in Use

```bash
# Change port in command:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Database Issues

```bash
# Delete database and reinitialize:
rm survey.db
python seed_db.py
```

### Virtual Environment Issues

```bash
# Deactivate and reactivate:
deactivate
.\venv\Scripts\Activate.ps1
```

### Permission Denied on .sh file (Linux/macOS)

```bash
chmod +x run.sh
./run.sh
```

## 📝 Example: Create & Submit Survey

### 1. Create Survey

```bash
curl -X POST http://localhost:8000/api/surveys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Feedback Form",
    "description": "Your feedback matters",
    "status": "active",
    "questions": [
      {
        "type": "multiple_choice",
        "title": "How did we do?",
        "required": true,
        "order": 1,
        "options": [
          {"label": "Great", "value": "great", "order": 1},
          {"label": "Good", "value": "good", "order": 2},
          {"label": "Fair", "value": "fair", "order": 3}
        ]
      }
    ]
  }'
```

### 2. Upload Image

```bash
curl -X POST http://localhost:8000/api/surveys/{survey_id}/upload-image \
  -H "Authorization: Bearer <token>" \
  -F "file=@image.jpg"
```

### 3. Submit Response

```bash
curl -X POST http://localhost:8000/api/surveys/{survey_id}/responses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "responses": {
      "question_1_id": "great"
    }
  }'
```

## ✨ Next Steps

1. **Update Clerk Keys**: Replace `CLERK_SECRET_KEY` and `CLERK_PUBLISHABLE_KEY` in `.env`
2. **Test Endpoints**: Use Swagger UI at http://localhost:8000/docs
3. **Create Surveys**: Use frontend or API to create surveys
4. **Submit Responses**: Start collecting responses from users
5. **View Results**: Check analytics at `GET /api/surveys/{id}/results`

## 🔗 Frontend & Backend Integration

Both applications are ready to work together:

**Frontend** (Next.js):

- 📍 Location: `C:\MyWork\Research\survey-app`
- 🚀 Start: `npm run dev` on port 3000
- Features: Survey list, detail page, form filling

**Backend** (FastAPI):

- 📍 Location: `C:\MyWork\Research\survey-api`
- 🚀 Start: Run `run.bat` or `run.sh` on port 8000
- Features: Survey CRUD, responses, analytics, image upload

## 📞 Support

For API documentation, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Check README.md for detailed API documentation.

---

**Backend Ready!** 🎉 Your FastAPI survey platform is ready for use.
