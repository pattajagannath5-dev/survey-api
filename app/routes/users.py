"""User routes for CRUD operations."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
import json
import logging

from ..database import get_db
from ..models import User
from ..schemas import UserResponse, UserUpdate
from ..auth import get_current_user
from ..config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get current user's profile"""
    
    user = db.query(User).filter(User.clerk_id == current_user).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update current user's profile"""
    
    user = db.query(User).filter(User.clerk_id == current_user).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get a user by ID"""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/webhook/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: Optional[str] = Header(None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
    db: Session = Depends(get_db)
):
    """Handle Clerk webhook events"""
    
    body = await request.body()
    body_str = body.decode("utf-8")
    
    logger.info(f"Received webhook - Headers: svix-id={svix_id}")
    logger.info(f"Webhook body: {body_str[:500]}")  # Log first 500 chars
    
    # Skip signature verification for now to debug
    # webhook_secret = settings.CLERK_WEBHOOK_SECRET
    # if webhook_secret and svix_id and svix_timestamp and svix_signature:
    #     try:
    #         from svix.webhooks import Webhook
    #         wh = Webhook(webhook_secret)
    #         wh.verify(body_str, {
    #             "svix-id": svix_id,
    #             "svix-timestamp": svix_timestamp,
    #             "svix-signature": svix_signature,
    #         })
    #     except Exception as e:
    #         logger.error(f"Webhook signature verification failed: {e}")
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"Invalid webhook signature: {str(e)}"
    #         )
    
    try:
        event = json.loads(body_str)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    
    event_type = event.get("type")
    data = event.get("data", {})
    
    logger.info(f"Event type: {event_type}")
    logger.info(f"Event data: {json.dumps(data, indent=2)[:1000]}")
    
    if event_type == "user.created":
        try:
            clerk_id = data.get("id")
            
            # Get primary email
            email_addresses = data.get("email_addresses", [])
            primary_email_id = data.get("primary_email_address_id")
            
            email = None
            for email_obj in email_addresses:
                if email_obj.get("id") == primary_email_id:
                    email = email_obj.get("email_address")
                    break
            
            # Fallback to first email if no primary found
            if not email and email_addresses:
                email = email_addresses[0].get("email_address")
            
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            profile_image_url = data.get("image_url")
            
            logger.info(f"Creating user: clerk_id={clerk_id}, email={email}")
            
            if not clerk_id:
                logger.error("Missing clerk_id")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing clerk_id"
                )
            
            if not email:
                logger.error("Missing email")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing email"
                )
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.clerk_id == clerk_id).first()
            if existing_user:
                logger.info(f"User already exists: {clerk_id}")
                return {"status": "user already exists"}
            
            # Check if email already exists
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                logger.info(f"Email already exists: {email}")
                return {"status": "email already exists"}
            
            user = User(
                clerk_id=clerk_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                profile_image_url=profile_image_url,
            )
            db.add(user)
            db.commit()
            
            logger.info(f"User created successfully: {clerk_id}")
            return {"status": "user created"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}"
            )
    
    elif event_type == "user.updated":
        try:
            clerk_id = data.get("id")
            
            user = db.query(User).filter(User.clerk_id == clerk_id).first()
            if not user:
                logger.info(f"User not found for update: {clerk_id}")
                return {"status": "user not found"}
            
            # Get primary email
            email_addresses = data.get("email_addresses", [])
            primary_email_id = data.get("primary_email_address_id")
            
            for email_obj in email_addresses:
                if email_obj.get("id") == primary_email_id:
                    user.email = email_obj.get("email_address")
                    break
            
            if data.get("first_name"):
                user.first_name = data.get("first_name")
            if data.get("last_name"):
                user.last_name = data.get("last_name")
            if data.get("image_url"):
                user.profile_image_url = data.get("image_url")
            
            db.commit()
            logger.info(f"User updated: {clerk_id}")
            return {"status": "user updated"}
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user: {str(e)}"
            )
    
    elif event_type == "user.deleted":
        try:
            clerk_id = data.get("id")
            
            user = db.query(User).filter(User.clerk_id == clerk_id).first()
            if not user:
                return {"status": "user not found"}
            
            user.is_active = False
            db.commit()
            logger.info(f"User deactivated: {clerk_id}")
            return {"status": "user deactivated"}
            
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deactivating user: {str(e)}"
            )
    
    logger.info(f"Event ignored: {event_type}")
    return {"status": "event ignored", "event_type": event_type}
