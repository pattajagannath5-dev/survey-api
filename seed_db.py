"""
Script to seed sample survey data
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Survey, Question, Option, SurveyStatus, QuestionType
from datetime import datetime
import uuid

def seed_database():
    """Create sample surveys"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if data already exists
    existing = db.query(Survey).first()
    if existing:
        print("Database already seeded. Skipping...")
        db.close()
        return
    
    # Create sample surveys
    user1_id = "user_demo_1"
    user2_id = "user_demo_2"
    
    # Survey 1: Customer Satisfaction
    survey1 = Survey(
        id=str(uuid.uuid4()),
        title="Customer Satisfaction Survey",
        description="Help us improve our service by sharing your feedback",
        created_by=user1_id,
        status=SurveyStatus.ACTIVE
    )
    
    q1 = Question(
        id=str(uuid.uuid4()),
        survey_id=survey1.id,
        type=QuestionType.MULTIPLE_CHOICE,
        title="How satisfied are you with our service?",
        required=True,
        order=1
    )
    q1.options = [
        Option(id=str(uuid.uuid4()), question_id=q1.id, label="Very Satisfied", value="very_satisfied", order=1),
        Option(id=str(uuid.uuid4()), question_id=q1.id, label="Satisfied", value="satisfied", order=2),
        Option(id=str(uuid.uuid4()), question_id=q1.id, label="Neutral", value="neutral", order=3),
        Option(id=str(uuid.uuid4()), question_id=q1.id, label="Dissatisfied", value="dissatisfied", order=4),
    ]
    
    q2 = Question(
        id=str(uuid.uuid4()),
        survey_id=survey1.id,
        type=QuestionType.RATING,
        title="Rate our product quality",
        required=True,
        order=2,
        min_value=1,
        max_value=5
    )
    
    q3 = Question(
        id=str(uuid.uuid4()),
        survey_id=survey1.id,
        type=QuestionType.TEXT,
        title="What can we improve?",
        required=False,
        order=3,
        placeholder="Share your suggestions..."
    )
    
    survey1.questions = [q1, q2, q3]
    
    # Survey 2: Product Features
    survey2 = Survey(
        id=str(uuid.uuid4()),
        title="What features would you like to see?",
        description="Vote on features you'd like us to build",
        created_by=user2_id,
        status=SurveyStatus.ACTIVE
    )
    
    q4 = Question(
        id=str(uuid.uuid4()),
        survey_id=survey2.id,
        type=QuestionType.CHECKBOX,
        title="Select features of interest",
        required=True,
        order=1
    )
    q4.options = [
        Option(id=str(uuid.uuid4()), question_id=q4.id, label="Dark Mode", value="dark_mode", order=1),
        Option(id=str(uuid.uuid4()), question_id=q4.id, label="Mobile App", value="mobile_app", order=2),
        Option(id=str(uuid.uuid4()), question_id=q4.id, label="API Access", value="api_access", order=3),
        Option(id=str(uuid.uuid4()), question_id=q4.id, label="Advanced Analytics", value="analytics", order=4),
    ]
    
    q5 = Question(
        id=str(uuid.uuid4()),
        survey_id=survey2.id,
        type=QuestionType.TEXT,
        title="Any other features?",
        required=False,
        order=2,
        placeholder="Tell us about other features..."
    )
    
    survey2.questions = [q4, q5]
    
    # Survey 3: User Experience
    survey3 = Survey(
        id=str(uuid.uuid4()),
        title="User Experience Feedback",
        description="Share your experience using our platform",
        created_by=user1_id,
        status=SurveyStatus.ACTIVE
    )
    
    q6 = Question(
        id=str(uuid.uuid4()),
        survey_id=survey3.id,
        type=QuestionType.RATING,
        title="Ease of use (1-10)",
        required=True,
        order=1,
        min_value=1,
        max_value=10
    )
    
    q7 = Question(
        id=str(uuid.uuid4()),
        survey_id=survey3.id,
        type=QuestionType.MULTIPLE_CHOICE,
        title="How did you hear about us?",
        required=True,
        order=2
    )
    q7.options = [
        Option(id=str(uuid.uuid4()), question_id=q7.id, label="Social Media", value="social", order=1),
        Option(id=str(uuid.uuid4()), question_id=q7.id, label="Friend Referral", value="friend", order=2),
        Option(id=str(uuid.uuid4()), question_id=q7.id, label="Search Engine", value="search", order=3),
        Option(id=str(uuid.uuid4()), question_id=q7.id, label="Advertisement", value="ad", order=4),
    ]
    
    survey3.questions = [q6, q7]
    
    # Add surveys to database
    db.add(survey1)
    db.add(survey2)
    db.add(survey3)
    
    db.commit()
    print("✓ Database seeded successfully with 3 sample surveys")
    db.close()

if __name__ == "__main__":
    seed_database()
