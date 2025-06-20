from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
from inference import Facet_Generator

log_file = "logs/app.log"

class ProcessRequest(BaseModel):
    data: Dict[str, Any]
    num_results: int
    prefiltering: bool
    llm_clean: bool

class ProcessedResult(BaseModel):
    result_1: Dict[str, Any]
    result_2: Dict[str, Any]
    
app = FastAPI(title="Facets Generator API")
generator = Facet_Generator()

@app.post("/generate", response_model=ProcessedResult)
async def process_endpoint(request: ProcessRequest):
    open(log_file, "w").close() #check conflicts when using async functionality
    result_1, result_2 = generator.inference(request.data, request.num_results, request.prefiltering, request.llm_clean)
    
    return ProcessedResult(
        result_1=result_1,
        result_2=result_2
    )

@app.get("/logs")
async def get_logs():
    with open(log_file, "r") as f:
        logs = f.read()
    return {"logs": logs}
    
@app.get("/")
async def root():
    return {"message": "Facets Generator API is running"}

    