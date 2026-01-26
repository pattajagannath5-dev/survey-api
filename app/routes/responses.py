from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import Survey, Question, Response, Answer
from ..schemas import (
    ResponseCreate,
    ResponseResponse,
    ResponseWithSurvey,
    AnswerCreate,
    AnswerResponse,
)
from ..auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/responses", tags=["responses"])


@router.get("/my-responses", response_model=List[ResponseWithSurvey])
async def get_my_responses(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get all responses submitted by the current user"""
    
    responses = db.query(Response).filter(
        Response.respondent_id == current_user
    ).order_by(Response.created_at.desc()).offset(skip).limit(limit).all()
    
    return responses


@router.get("/{response_id}", response_model=ResponseResponse)
async def get_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get a specific response by ID"""
    
    response = db.query(Response).filter(Response.id == response_id).first()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    survey = db.query(Survey).filter(Survey.id == response.survey_id).first()
    
    if response.respondent_id != current_user and survey.creator_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this response"
        )
    
    return response
