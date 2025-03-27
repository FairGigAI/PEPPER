"""Backend agent for handling backend development tasks."""

from typing import Dict, Any
import os
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from core.agent_base import BaseAgent, Task

class BackendAgent(BaseAgent):
    """Agent responsible for backend development tasks."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.console = Console()
        self.output_dir = "src/backend"
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing backend task: {task.task_id}")
        return {}
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the backend task."""
        logger.info(f"Executing backend task: {task.task_id}")
        
        if task.task_type == "backend.api_development":
            return await self._create_fastapi_route(task)
        else:
            raise ValueError(f"Unsupported task type: {task.task_type}")
            
    async def _create_fastapi_route(self, task: Task) -> Dict[str, Any]:
        """Create a new FastAPI route."""
        # Extract route name from description
        route_name = task.description.split()[-1].lower()
        file_name = f"{route_name}_route.py"
        file_path = os.path.join(self.output_dir, file_name)
        
        # Generate route code
        route_code = f"""from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/{route_name}",
    tags=["{route_name}"]
)

class {route_name.capitalize()}Response(BaseModel):
    id: int
    title: str
    description: str
    status: str

@router.get("/", response_model=List[{route_name.capitalize()}Response])
async def get_all_{route_name}():
    '''Get all {route_name} entries'''
    # Sample response
    return [
        {route_name.capitalize()}Response(
            id=1,
            title="Sample {route_name}",
            description="This is a sample {route_name}",
            status="active"
        )
    ]

@router.get("/{{item_id}}", response_model={route_name.capitalize()}Response)
async def get_{route_name}_by_id(item_id: int):
    '''Get a specific {route_name} by ID'''
    # Sample response
    return {route_name.capitalize()}Response(
        id=item_id,
        title=f"Sample {route_name} {{item_id}}",
        description=f"This is a sample {route_name} with ID {{item_id}}",
        status="active"
    )
"""
        
        # Write file
        try:
            with open(file_path, 'w') as f:
                f.write(route_code)
            logger.info(f"Created FastAPI route: {file_path}")
            
            return {
                "status": "success",
                "message": f"Created FastAPI route for {route_name}",
                "details": {
                    "route_file": file_path,
                    "route_name": route_name,
                    "endpoints": [
                        f"GET /{route_name}/",
                        f"GET /{route_name}/{{item_id}}"
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Failed to create route: {e}")
            raise
        
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing backend task: {task.task_id}")
        return result

    async def run_task(self, task: Task) -> Dict[str, Any]:
        """Execute backend development tasks."""
        self.log_task_start(task)
        
        try:
            if task.task_type == "backend.api_development":
                return await self._create_fastapi_route(task)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
            
        except Exception as e:
            await self.handle_error(task, e)
            
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare backend tasks."""
        if task.task_type not in ["backend.api_development", "backend.database", "backend.microservices"]:
            raise ValueError(f"Unsupported task type: {task.task_type}")
        return task 