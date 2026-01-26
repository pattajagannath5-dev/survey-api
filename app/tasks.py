"""Celery tasks for async processing."""
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Survey, Response, User
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_survey_notification(self, survey_id: str, notification_type: str, user_id: str = None):
    """
    Send notifications for survey events.
    
    notification_type: 'new_response', 'survey_published', 'survey_closed'
    """
    try:
        db = SessionLocal()
        try:
            survey = db.query(Survey).filter(Survey.id == survey_id).first()
            if not survey:
                logger.warning(f"Survey {survey_id} not found for notification")
                return {"status": "error", "message": "Survey not found"}
            
            # Get the survey creator
            creator = db.query(User).filter(User.id == survey.created_by).first()
            
            if notification_type == "new_response":
                # Notify survey creator about new response
                message = f"New response received for survey: {survey.title}"
                logger.info(f"Notification: {message} for user {creator.email if creator else 'unknown'}")
                
            elif notification_type == "survey_published":
                # Notify about survey being published
                message = f"Survey '{survey.title}' is now live!"
                logger.info(f"Notification: {message}")
                
            elif notification_type == "survey_closed":
                # Notify about survey being closed
                message = f"Survey '{survey.title}' has been closed. Total responses: {survey.response_count}"
                logger.info(f"Notification: {message}")
            
            return {"status": "success", "message": message}
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Error sending notification: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def process_survey_analytics(self, survey_id: str):
    """
    Process and cache survey analytics.
    """
    try:
        db = SessionLocal()
        try:
            survey = db.query(Survey).filter(Survey.id == survey_id).first()
            if not survey:
                return {"status": "error", "message": "Survey not found"}
            
            responses = db.query(Response).filter(Response.survey_id == survey_id).all()
            total_responses = len(responses)
            
            analytics = {
                "survey_id": survey_id,
                "total_responses": total_responses,
                "questions": [],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            for question in survey.questions:
                question_stats = {
                    "question_id": question.id,
                    "question_title": question.title,
                    "question_type": question.type,
                    "response_stats": []
                }
                
                if question.type in ["multiple_choice", "checkbox"]:
                    option_counts = {opt.value: 0 for opt in question.options}
                    
                    for response in responses:
                        answer = response.responses.get(question.id)
                        if answer:
                            if isinstance(answer, list):
                                for val in answer:
                                    if val in option_counts:
                                        option_counts[val] += 1
                            elif answer in option_counts:
                                option_counts[answer] += 1
                    
                    for option in question.options:
                        count = option_counts.get(option.value, 0)
                        percentage = (count / total_responses * 100) if total_responses > 0 else 0
                        question_stats["response_stats"].append({
                            "label": option.label,
                            "value": option.value,
                            "count": count,
                            "percentage": round(percentage, 1)
                        })
                
                elif question.type == "rating":
                    min_val = question.min_value or 1
                    max_val = question.max_value or 5
                    rating_counts = {str(i): 0 for i in range(min_val, max_val + 1)}
                    total_rating = 0
                    rating_responses = 0
                    
                    for response in responses:
                        answer = response.responses.get(question.id)
                        if answer is not None:
                            rating_counts[str(answer)] = rating_counts.get(str(answer), 0) + 1
                            total_rating += int(answer)
                            rating_responses += 1
                    
                    average_rating = total_rating / rating_responses if rating_responses > 0 else 0
                    question_stats["average_rating"] = round(average_rating, 2)
                    
                    for rating, count in sorted(rating_counts.items()):
                        percentage = (count / total_responses * 100) if total_responses > 0 else 0
                        question_stats["response_stats"].append({
                            "value": rating,
                            "count": count,
                            "percentage": round(percentage, 1)
                        })
                
                else:  # text responses
                    text_responses = []
                    for response in responses:
                        answer = response.responses.get(question.id)
                        if answer:
                            text_responses.append(answer)
                    
                    question_stats["text_responses"] = text_responses
                    question_stats["response_count"] = len(text_responses)
                
                analytics["questions"].append(question_stats)
            
            # Cache the analytics in Redis
            from app.redis_client import redis_client
            cache_key = f"survey_analytics:{survey_id}"
            redis_client.setex(cache_key, 300, json.dumps(analytics))  # Cache for 5 minutes
            
            logger.info(f"Analytics processed and cached for survey {survey_id}")
            return analytics
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Error processing analytics: {exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, max_retries=3)
def export_survey_results(self, survey_id: str, format: str = "json"):
    """
    Export survey results to a file (JSON or CSV).
    """
    try:
        db = SessionLocal()
        try:
            survey = db.query(Survey).filter(Survey.id == survey_id).first()
            if not survey:
                return {"status": "error", "message": "Survey not found"}
            
            responses = db.query(Response).filter(Response.survey_id == survey_id).all()
            
            export_data = {
                "survey": {
                    "id": survey.id,
                    "title": survey.title,
                    "description": survey.description,
                    "status": survey.status,
                    "created_at": survey.created_at.isoformat(),
                    "total_responses": len(responses)
                },
                "questions": [
                    {
                        "id": q.id,
                        "title": q.title,
                        "type": q.type,
                        "options": [{"label": o.label, "value": o.value} for o in q.options]
                    }
                    for q in survey.questions
                ],
                "responses": [
                    {
                        "id": r.id,
                        "submitted_at": r.submitted_at.isoformat(),
                        "answers": r.responses
                    }
                    for r in responses
                ]
            }
            
            if format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Header row
                headers = ["Response ID", "Submitted At"] + [q.title for q in survey.questions]
                writer.writerow(headers)
                
                # Data rows
                for response in responses:
                    row = [response.id, response.submitted_at.isoformat()]
                    for question in survey.questions:
                        answer = response.responses.get(question.id, "")
                        if isinstance(answer, list):
                            answer = ", ".join(answer)
                        row.append(str(answer))
                    writer.writerow(row)
                
                export_data = output.getvalue()
            
            logger.info(f"Export completed for survey {survey_id}")
            return {"status": "success", "data": export_data, "format": format}
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Error exporting survey: {exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task
def cleanup_expired_surveys():
    """
    Periodic task to close expired surveys.
    """
    db = SessionLocal()
    try:
        expired_surveys = db.query(Survey).filter(
            Survey.status == "active",
            Survey.expires_at <= datetime.utcnow()
        ).all()
        
        for survey in expired_surveys:
            survey.status = "closed"
            logger.info(f"Closed expired survey: {survey.id}")
        
        db.commit()
        return {"status": "success", "closed_count": len(expired_surveys)}
        
    finally:
        db.close()


@celery_app.task
def sync_user_from_clerk(user_data: dict):
    """
    Sync user data from Clerk webhook.
    """
    db = SessionLocal()
    try:
        user_id = user_data.get("id")
        email = user_data.get("email_addresses", [{}])[0].get("email_address", "")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        image_url = user_data.get("image_url", "")
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.profile_image_url = image_url
            user.updated_at = datetime.utcnow()
        else:
            user = User(
                id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                profile_image_url=image_url
            )
            db.add(user)
        
        db.commit()
        logger.info(f"User synced from Clerk: {user_id}")
        return {"status": "success", "user_id": user_id}
        
    finally:
        db.close()
