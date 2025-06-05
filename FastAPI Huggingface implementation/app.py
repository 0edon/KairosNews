import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from models.embedding import EmbeddingModel
from models.summarization import SummarizationModel
from models.nlp import NLPModel
from database.query import DatabaseService
from main import QueryProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize models
embedding_model = None
summarization_model = None
nlp_model = None
db_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedding_model, summarization_model, nlp_model, db_service
    
    # Model initialization
    logger.info("Initializing models...")
    try:
        embedding_model = EmbeddingModel()
        summarization_model = SummarizationModel()
        nlp_model = NLPModel()
        db_service = DatabaseService()
        logger.info("All models initialized successfully")
    except Exception as e:
        logger.error(f"Model initialization failed: {str(e)}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down application...")
    if db_service:
        try:
            await db_service.close()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")

app = FastAPI(
    title="Kairos News API",
    version="1.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Kairos News API is running"}
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage
jobs_db: Dict[str, Dict] = {}

class PostRequest(BaseModel):
    query: str
    topic: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class JobStatus(BaseModel):
    id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    request: PostRequest
    result: Optional[Dict[str, Any]] = None

@app.post("/index", response_model=JobStatus)
async def create_job(request: PostRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    logger.info(f"Creating new job {job_id} with request: {request.dict()}")

    jobs_db[job_id] = {
        "id": job_id,
        "status": "processing",
        "created_at": datetime.now(),
        "completed_at": None,
        "request": request.dict(),
        "result": None
    }

    background_tasks.add_task(
        process_job,
        job_id,
        request,
        embedding_model,
        summarization_model,
        nlp_model,
        db_service
    )
    
    logger.info(f"Job {job_id} created and processing started")
    return jobs_db[job_id]

@app.get("/loading", response_model=JobStatus)
async def get_job_status(id: str):
    logger.info(f"Checking status for job {id}")
    if id not in jobs_db:
        logger.warning(f"Job {id} not found")
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"Returning status for job {id}: {jobs_db[id]['status']}")
    return jobs_db[id]

async def process_job(
    job_id: str,
    request: PostRequest,
    embedding_model: EmbeddingModel,
    summarization_model: SummarizationModel,
    nlp_model: NLPModel,
    db_service: DatabaseService
):
    try:
        logger.info(f"Starting processing for job {job_id}")
        
        processor = QueryProcessor(
            embedding_model=embedding_model,
            summarization_model=summarization_model,
            nlp_model=nlp_model,
            db_service=db_service
        )
        
        logger.debug(f"Processing query: {request.query}")
        result = await processor.process(
            query=request.query,
            topic=request.topic,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        jobs_db[job_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "result": result if result else {"message": "No results found"}
        })
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
        jobs_db[job_id].update({
            "status": "failed",
            "completed_at": datetime.now(),
            "result": {"error": str(e)}
        })
        logger.info(f"Job {job_id} marked as failed")