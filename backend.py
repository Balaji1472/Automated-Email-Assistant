"""
FastAPI backend server for the AI Communication Assistant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
from contextlib import asynccontextmanager

from email_handler import fetch_support_emails, get_email_counts
from ai_core import get_ai_core

# Lifespan manager for startup events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup logic. Initializes the RAG pipeline.
    """
    # Code to run on startup
    try:
        ai_core = get_ai_core()
        ai_core.setup_and_run_rag("knowledge_base.txt")
        print(" AI Core initialized successfully")
    except Exception as e:
        print(f" Error initializing AI Core: {str(e)}")
    yield
    # Code to run on shutdown (if any) could go here

# Initialize FastAPI app with the new lifespan manager
app = FastAPI(
    title="AI Communication Assistant API",
    description="Backend API for processing customer support emails with AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessedEmail(BaseModel):
    """Pydantic model for processed email response."""
    id: str
    sender: str
    subject: str
    date: str
    body: str
    sentiment: str
    priority: str
    summary: str
    extracted_info: Dict[str, Any]
    draft_response: str

class ProcessEmailsResponse(BaseModel):
    """Response model for the process emails endpoint."""
    emails: List[ProcessedEmail]
    total_count: int
    urgent_count: int
    negative_sentiment_count: int

class EmailStatsResponse(BaseModel):
    """Response model for email statistics."""
    unread_count: int
    read_count: int
    total_count: int

@app.get("/email-stats", response_model=EmailStatsResponse)
async def get_email_statistics():
    """
    Get email count statistics.
    
    Returns:
        Email count statistics
    """
    try:
        unread_count, read_count = get_email_counts()
        total_count = unread_count + read_count
        
        return EmailStatsResponse(
            unread_count=unread_count,
            read_count=read_count,
            total_count=total_count
        )
    except Exception as e:
        print(f" Error getting email statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting email statistics: {str(e)}")

@app.post("/process-emails", response_model=ProcessEmailsResponse)
async def process_emails():
    """
    Fetch and process support emails with AI analysis.
    
    Returns:
        Processed emails with AI analysis and draft responses
    """
    try:
        # Get AI core instance
        ai_core = get_ai_core()
        
        # Fetch emails from Gmail
        print(" Fetching support emails...")
        emails = fetch_support_emails()
        
        if not emails:
            print(" No new unread emails found.")
            return ProcessEmailsResponse(
                emails=[],
                total_count=0,
                urgent_count=0,
                negative_sentiment_count=0
            )
        
        print(f" Processing {len(emails)} emails with AI...")
        processed_emails = []
        successful_count = 0
        
        # Process each email with AI
        for i, email_data in enumerate(emails, 1):
            try:
                print(f"Processing email {i}/{len(emails)}: {email_data['subject'][:50]}...")
                
                # Analyze email content
                analysis = ai_core.analyze_email_content(email_data['body'])
                print(f"  - Analysis complete: {analysis['sentiment']} sentiment, {analysis['priority']} priority")
                
                # Generate draft response
                draft_response = ai_core.generate_contextual_response(
                    analysis,
                    email_data['body']
                )
                print(f"  - Draft response generated")
                
                # Create processed email object
                processed_email = ProcessedEmail(
                    id=email_data['id'],
                    sender=email_data['sender'],
                    subject=email_data['subject'],
                    date=email_data['date'],
                    body=email_data['body'],
                    sentiment=analysis['sentiment'],
                    priority=analysis['priority'],
                    summary=analysis['summary'],
                    extracted_info=analysis['extracted_info'],
                    draft_response=draft_response
                )
                
                processed_emails.append(processed_email)
                successful_count += 1
                
            except Exception as e:
                print(f" Error processing email {email_data['id']}: {str(e)}")
                # Continue processing other emails instead of failing completely
                continue
        
        if successful_count == 0:
            raise HTTPException(status_code=500, detail="Failed to process any emails successfully")
        
        # Sort emails by priority (urgent first), then by sentiment (negative first)
        processed_emails.sort(key=lambda x: (
            x.priority != 'Urgent',  # Urgent emails first
            x.sentiment != 'Negative'  # Negative sentiment second
        ))
        
        # Calculate metrics
        total_count = len(processed_emails)
        urgent_count = sum(1 for email in processed_emails if email.priority == 'Urgent')
        negative_sentiment_count = sum(1 for email in processed_emails if email.sentiment == 'Negative')
        
        print(f" Successfully processed {successful_count} out of {len(emails)} emails.")
        print(f"   - Urgent: {urgent_count}")
        print(f"   - Negative sentiment: {negative_sentiment_count}")
        
        return ProcessEmailsResponse(
            emails=processed_emails,
            total_count=total_count,
            urgent_count=urgent_count,
            negative_sentiment_count=negative_sentiment_count
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f" Top-level error in process_emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing emails: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        ai_core = get_ai_core()
        return {
            "status": "healthy", 
            "message": "AI Communication Assistant API is running",
            "ai_core_initialized": ai_core is not None,
            "knowledge_base_loaded": ai_core.collection is not None if ai_core else False
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}"
        }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Communication Assistant API",
        "version": "1.0.0",
        "description": "Backend API for processing customer support emails with AI",
        "endpoints": {
            "health": "/health",
            "email_stats": "/email-stats", 
            "process_emails": "/process-emails"
        }
    }

if __name__ == "__main__":
    # This block is for direct execution, but using 'uvicorn backend:app --reload' is recommended
    uvicorn.run(app, host="127.0.0.1", port=8000)