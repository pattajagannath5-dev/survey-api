from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class SurveyStatus(str, Enum):
    draft = "draft"
    active = "active"
    closed = "closed"


class QuestionType(str, Enum):
    text = "text"
    rating = "rating"
    single_select = "single_select"
    multiple_select = "multiple_select"


# Question Option Schema
class QuestionOptionSchema(BaseModel):
    text: str
    value: str


# Question Schemas
class QuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType = QuestionType.text
    description: Optional[str] = None
    is_required: bool = False
    order_number: int = 0
    options: Optional[List[QuestionOptionSchema]] = None
    validation_rules: Optional[dict] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    order_number: Optional[int] = None
    options: Optional[List[QuestionOptionSchema]] = None
    validation_rules: Optional[dict] = None


class QuestionResponse(QuestionBase):
    id: int
    survey_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Image Schemas
class ImageResponse(BaseModel):
    id: int
    filename: str
    url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SurveyImageSchema(BaseModel):
    id: int
    filename: str
    filepath: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Survey Schemas
class SurveyBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[SurveyStatus] = SurveyStatus.draft
    allow_anonymous: bool = False
    expires_at: Optional[datetime] = None
    max_responses: Optional[int] = None


class SurveyCreate(SurveyBase):
    questions: Optional[List[QuestionCreate]] = None


class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SurveyStatus] = None
    allow_anonymous: Optional[bool] = None
    expires_at: Optional[datetime] = None
    max_responses: Optional[int] = None


class SurveyResponse(SurveyBase):
    id: int
    creator_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    questions: List[QuestionResponse] = []
    images: List[SurveyImageSchema] = []
    response_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SurveyListResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    creator_id: str
    created_at: datetime
    response_count: int = 0
    allow_anonymous: bool = False
    images: List[SurveyImageSchema] = []

    model_config = ConfigDict(from_attributes=True)


# Answer Schemas
class AnswerBase(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    answer_rating: Optional[int] = None
    answer_options: Optional[List[str]] = None


class AnswerCreate(AnswerBase):
    pass


class AnswerResponse(AnswerBase):
    id: int
    response_id: int

    model_config = ConfigDict(from_attributes=True)


# Response Schemas
class ResponseBase(BaseModel):
    is_anonymous: bool = False


class ResponseCreate(ResponseBase):
    answers: List[AnswerCreate]


class ResponseResponse(ResponseBase):
    id: int
    survey_id: int
    respondent_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    answers: List[AnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)


# User Schemas
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    clerk_id: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: int
    clerk_id: str
    avatar_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Survey Basic (for embedding in responses)
class SurveyBasic(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    
    model_config = ConfigDict(from_attributes=True)


# Response with Survey info
class ResponseWithSurvey(BaseModel):
    id: int
    survey_id: int
    respondent_id: Optional[str] = None
    is_anonymous: bool
    created_at: datetime
    completed_at: Optional[datetime] = None
    survey: Optional[SurveyBasic] = None
    answers: List[AnswerResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

