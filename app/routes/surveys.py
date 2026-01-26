from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime

from ..database import get_db
from ..models import Survey, Question, SurveyImage, Response, Answer
from ..schemas import (
    SurveyCreate, SurveyUpdate, SurveyResponse, SurveyListResponse,
    QuestionCreate, QuestionUpdate, QuestionResponse, ImageResponse,
    ResponseCreate, ResponseResponse
)
from ..auth import get_current_user, get_optional_user
from ..config import settings

router = APIRouter(prefix="/api/surveys", tags=["surveys"])

# IMPORTANT: This must come BEFORE the /{survey_id} route
@router.get("/stats/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get dashboard statistics for the current user"""
    
    total_surveys = db.query(Survey).filter(Survey.creator_id == current_user).count()
    active_surveys = db.query(Survey).filter(
        Survey.creator_id == current_user,
        Survey.status == "active"
    ).count()
    
    user_survey_ids = db.query(Survey.id).filter(Survey.creator_id == current_user).subquery()
    total_responses = db.query(Response).filter(
        Response.survey_id.in_(user_survey_ids)
    ).count()
    
    my_responses = db.query(Response).filter(
        Response.respondent_id == current_user
    ).count()
    
    recent_surveys = db.query(Survey).filter(
        Survey.creator_id == current_user
    ).order_by(Survey.created_at.desc()).limit(5).all()
    
    recent_responses = db.query(Response).filter(
        Response.survey_id.in_(user_survey_ids)
    ).order_by(Response.created_at.desc()).limit(5).all()
    
    return {
        "total_surveys": total_surveys,
        "active_surveys": active_surveys,
        "total_responses": total_responses,
        "my_responses": my_responses,
        "recent_surveys": [
            {
                "id": s.id,
                "title": s.title,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
                "response_count": len(s.responses) if hasattr(s, 'responses') and s.responses else 0
            }
            for s in recent_surveys
        ],
        "recent_responses": [
            {
                "id": r.id,
                "survey_id": r.survey_id,
                "created_at": r.created_at.isoformat(),
                "is_anonymous": r.is_anonymous
            }
            for r in recent_responses
        ]
    }


@router.post("", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_survey(
    survey_data: SurveyCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create a new survey with optional questions"""
    
    # Create survey
    survey = Survey(
        title=survey_data.title,
        description=survey_data.description,
        status=survey_data.status.value if survey_data.status else "draft",
        creator_id=current_user,
        allow_anonymous=survey_data.allow_anonymous,
        expires_at=survey_data.expires_at,
        max_responses=survey_data.max_responses,
    )
    
    db.add(survey)
    db.flush()
    
    if survey_data.questions:
        for q_data in survey_data.questions:
            options_data = None
            if q_data.options:
                options_data = [
                    {"text": opt.text, "value": opt.value} 
                    for opt in q_data.options
                ]
            
            validation_data = None
            if q_data.validation_rules:
                if hasattr(q_data.validation_rules, 'model_dump'):
                    validation_data = q_data.validation_rules.model_dump()
                elif isinstance(q_data.validation_rules, dict):
                    validation_data = q_data.validation_rules
                else:
                    validation_data = dict(q_data.validation_rules)
            
            question = Question(
                survey_id=survey.id,
                question_text=q_data.question_text,
                question_type=q_data.question_type.value if q_data.question_type else "text",
                description=q_data.description,
                is_required=q_data.is_required,
                order_number=q_data.order_number,
                options=options_data,
                validation_rules=validation_data,
            )
            db.add(question)
    
    db.commit()
    db.refresh(survey)
    
    return survey


@router.get("", response_model=List[SurveyListResponse])
async def list_surveys(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    creator_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """List all surveys with optional filters"""
    
    query = db.query(Survey)
    
    if status:
        query = query.filter(Survey.status == status)
    
    if creator_id:
        query = query.filter(Survey.creator_id == creator_id)
    
    if current_user:
        query = query.filter(
            (Survey.status == "active") | (Survey.creator_id == current_user)
        )
    else:
        query = query.filter(Survey.status == "active")
    
    surveys = query.order_by(Survey.created_at.desc()).offset(skip).limit(limit).all()
    
    return surveys


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """Get a specific survey by ID"""
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    if survey.status != "active" and survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this survey"
        )
    
    return survey


@router.put("/{survey_id}", response_model=SurveyResponse)
async def update_survey(
    survey_id: int,
    survey_data: SurveyUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update a survey"""
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    if survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this survey"
        )
    
    update_data = survey_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(survey, field):
            if field == 'status' and value:
                setattr(survey, field, value.value if hasattr(value, 'value') else value)
            else:
                setattr(survey, field, value)
    
    survey.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(survey)
    
    return survey


@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Delete a survey"""
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    if survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this survey"
        )
    
    db.delete(survey)
    db.commit()
    
    return None


# Question endpoints
@router.post("/{survey_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_question(
    survey_id: int,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Add a question to a survey"""
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    if survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this survey"
        )
    
    options_data = None
    if question_data.options:
        options_data = [
            {"text": opt.text, "value": opt.value} 
            for opt in question_data.options
        ]
    
    validation_data = None
    if question_data.validation_rules:
        if hasattr(question_data.validation_rules, 'model_dump'):
            validation_data = question_data.validation_rules.model_dump()
        elif isinstance(question_data.validation_rules, dict):
            validation_data = question_data.validation_rules
        else:
            validation_data = dict(question_data.validation_rules)
    
    question = Question(
        survey_id=survey_id,
        question_text=question_data.question_text,
        question_type=question_data.question_type.value if question_data.question_type else "text",
        description=question_data.description,
        is_required=question_data.is_required,
        order_number=question_data.order_number,
        options=options_data,
        validation_rules=validation_data,
    )
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    return question


@router.put("/{survey_id}/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    survey_id: int,
    question_id: int,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update a question"""
    
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.survey_id == survey_id
    ).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this survey"
        )
    
    update_data = question_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(question, field):
            if field == 'question_type' and value:
                setattr(question, field, value.value if hasattr(value, 'value') else value)
            elif field == 'options' and value:
                options_data = [
                    {"text": opt.text, "value": opt.value} if hasattr(opt, 'text') else opt
                    for opt in value
                ]
                setattr(question, field, options_data)
            elif field == 'validation_rules' and value:
                if hasattr(value, 'model_dump'):
                    setattr(question, field, value.model_dump())
                elif isinstance(value, dict):
                    setattr(question, field, value)
                else:
                    setattr(question, field, dict(value))
            else:
                setattr(question, field, value)
    
    db.commit()
    db.refresh(question)
    
    return question


@router.delete("/{survey_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    survey_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Delete a question"""
    
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.survey_id == survey_id
    ).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this survey"
        )
    
    db.delete(question)
    db.commit()
    
    return None


# Survey Response endpoints
@router.post("/{survey_id}/responses", response_model=ResponseResponse, status_code=status.HTTP_201_CREATED)
async def submit_response(
    survey_id: int,
    response_data: ResponseCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_optional_user)
):
    """Submit a response to a survey"""
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    if survey.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Survey is not active"
        )
    
    # Check if anonymous is allowed
    if response_data.is_anonymous and not survey.allow_anonymous:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This survey does not allow anonymous responses"
        )
    
    # Check if user has already responded (only for non-anonymous responses)
    if current_user and not response_data.is_anonymous:
        existing_response = db.query(Response).filter(
            Response.survey_id == survey_id,
            Response.respondent_id == current_user
        ).first()
        
        if existing_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already submitted a response to this survey"
            )
    
    # For non-anonymous responses, user must be logged in
    if not response_data.is_anonymous and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be logged in to submit a non-anonymous response"
        )
    
    # Create response
    respondent_id = None if response_data.is_anonymous else current_user
    
    survey_response = Response(
        survey_id=survey_id,
        respondent_id=respondent_id,
        is_anonymous=response_data.is_anonymous,
        completed_at=datetime.utcnow(),
    )
    
    db.add(survey_response)
    db.flush()
    
    # Add answers
    for answer_data in response_data.answers:
        answer = Answer(
            response_id=survey_response.id,
            question_id=answer_data.question_id,
            answer_text=answer_data.answer_text,
            answer_rating=answer_data.answer_rating,
            answer_options=answer_data.answer_options,
        )
        db.add(answer)
    
    db.commit()
    db.refresh(survey_response)
    
    return survey_response


# Add endpoint to check if user has already responded
@router.get("/{survey_id}/my-response")
async def check_my_response(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Check if the current user has already responded to a survey"""
    
    existing_response = db.query(Response).filter(
        Response.survey_id == survey_id,
        Response.respondent_id == current_user
    ).first()
    
    if existing_response:
        return {
            "has_responded": True,
            "response_id": existing_response.id,
            "responded_at": existing_response.created_at.isoformat()
        }
    
    return {
        "has_responded": False,
        "response_id": None,
        "responded_at": None
    }


# Image endpoints
@router.post("/{survey_id}/images", response_model=List[ImageResponse])
async def upload_images(
    survey_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Upload images for a survey"""
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    if survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this survey"
        )
    
    uploaded_images = []
    upload_dir = settings.UPLOAD_DIRECTORY
    os.makedirs(upload_dir, exist_ok=True)
    
    for file in files:
        allowed_types = settings.ALLOWED_IMAGE_TYPES.split(',')
        if file.content_type not in allowed_types:
            continue
        
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        image = SurveyImage(
            survey_id=survey_id,
            filename=filename,
            filepath=filepath,
        )
        db.add(image)
        uploaded_images.append(image)
    
    db.commit()
    
    for img in uploaded_images:
        db.refresh(img)
    
    return [
        ImageResponse(
            id=img.id,
            filename=img.filename,
            url=f"/uploads/{img.filename}",
            created_at=img.created_at
        )
        for img in uploaded_images
    ]


@router.get("/{survey_id}/images", response_model=List[ImageResponse])
async def get_survey_images(
    survey_id: int,
    db: Session = Depends(get_db)
):
    """Get all images for a survey"""
    
    images = db.query(SurveyImage).filter(SurveyImage.survey_id == survey_id).all()
    
    return [
        ImageResponse(
            id=img.id,
            filename=img.filename,
            url=f"/uploads/{img.filename}",
            created_at=img.created_at
        )
        for img in images
    ]


@router.get("/{survey_id}/responses")
async def get_survey_responses(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get all responses for a survey (only for survey owner)"""
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    # Only allow survey owner to view responses
    if survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view responses for this survey"
        )
    
    responses = db.query(Response).filter(Response.survey_id == survey_id).all()
    
    # Build response data with answers
    response_data = []
    for resp in responses:
        answers_data = []
        for answer in resp.answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            answers_data.append({
                "id": answer.id,
                "question_id": answer.question_id,
                "question_text": question.question_text if question else None,
                "question_type": question.question_type if question else None,
                "answer_text": answer.answer_text,
                "answer_rating": answer.answer_rating,
                "answer_options": answer.answer_options,
            })
        
        response_data.append({
            "id": resp.id,
            "survey_id": resp.survey_id,
            "respondent_id": resp.respondent_id,
            "is_anonymous": resp.is_anonymous,
            "created_at": resp.created_at.isoformat(),
            "completed_at": resp.completed_at.isoformat() if resp.completed_at else None,
            "answers": answers_data,
        })
    
    return {
        "survey": {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "status": survey.status,
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "order_number": q.order_number,
                    "options": q.options,
                }
                for q in sorted(survey.questions, key=lambda x: x.order_number)
            ],
        },
        "responses": response_data,
        "total_responses": len(response_data),
    }

