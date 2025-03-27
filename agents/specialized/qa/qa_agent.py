from typing import Dict, Any, List
import os
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.agent_base import BaseAgent, Task
from validators.react_validator import validate_component
from validators.api_validator import validate_endpoint

class QAAgent(BaseAgent):
    """Agent responsible for testing and validation tasks."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.console = Console()
        self.backend_output_dir = "output/backend"
        self.required_keywords = {
            "endpoint": ["endpoint", "route", "path"],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "framework": ["fastapi", "flask", "django"],
            "documentation": ["#", "##", "```"]
        }
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the QA task."""
        logger.info(f"Preprocessing QA task: {task.task_id}")
        return {}
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the QA task."""
        logger.info(f"Executing QA task: {task.task_id}")
        
        if task.task_type == "qa.frontend_validation":
            return await self._validate_frontend(task)
        elif task.task_type == "qa.backend_validation":
            return await self._validate_backend(task)
        else:
            raise ValueError(f"Unsupported task type: {task.task_type}")
            
    async def _validate_frontend(self, task: Task) -> Dict[str, Any]:
        """Validate frontend components."""
        file_path = task.metadata.get("file_path")
        if not file_path:
            return {
                "status": "FAIL",
                "reason": "No file path provided in task metadata"
            }
            
        result = validate_component(file_path)
        logger.info(f"Frontend validation result: {result['status']} - {result['reason']}")
        return result
        
    async def _validate_backend(self, task: Task) -> Dict[str, Any]:
        """Validate backend endpoints."""
        file_path = task.metadata.get("file_path")
        if not file_path:
            return {
                "status": "FAIL",
                "reason": "No file path provided in task metadata"
            }
            
        result = validate_endpoint(file_path)
        logger.info(f"Backend validation result: {result['status']} - {result['reason']}")
        return result
        
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the QA results."""
        logger.info(f"Postprocessing QA task: {task.task_id}")
        return result

    async def run_task(self, task: Task) -> Dict[str, Any]:
        """Execute QA tasks."""
        self.log_task_start(task)
        
        try:
            if task.task_type == "qa.frontend_validation":
                return await self._validate_frontend(task)
            elif task.task_type == "qa.backend_validation":
                return await self._validate_backend(task)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
            
        except Exception as e:
            await self.handle_error(task, e)
            
    def _find_latest_backend_file(self) -> str:
        """Find the most recent backend output file."""
        try:
            files = os.listdir(self.backend_output_dir)
            if not files:
                return None
                
            # Filter for API endpoint files and get the most recent
            api_files = [f for f in files if f.startswith("api_endpoint_")]
            if not api_files:
                return None
                
            latest_file = max(api_files, key=lambda x: os.path.getctime(
                os.path.join(self.backend_output_dir, x)
            ))
            
            return os.path.join(self.backend_output_dir, latest_file)
            
        except Exception as e:
            self.logger.error(f"Error finding latest backend file: {e}")
            return None
            
    async def _validate_backend_output(self, filepath: str) -> Dict[str, Any]:
        """Validate the backend output file against required criteria."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            validation_results = {}
            total_checks = 0
            passed_checks = 0
            
            # Check each category of required keywords
            for category, keywords in self.required_keywords.items():
                found_keywords = []
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        found_keywords.append(keyword)
                        
                validation_results[category] = {
                    "required": keywords,
                    "found": found_keywords,
                    "passed": len(found_keywords) > 0
                }
                
                total_checks += 1
                if validation_results[category]["passed"]:
                    passed_checks += 1
                    
            # Calculate overall pass rate
            pass_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            return {
                "status": "PASS" if pass_rate >= 80 else "FAIL",
                "pass_rate": pass_rate,
                "file": filepath,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "validation_results": validation_results
            }
            
        except Exception as e:
            self.logger.error(f"Error validating backend output: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "file": filepath,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
    def _log_validation_results(self, results: Dict[str, Any]):
        """Log validation results with rich formatting."""
        # Create a table for validation results
        table = Table(title="QA Validation Results")
        table.add_column("Category", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Found Keywords", style="yellow")
        
        if "validation_results" in results:
            for category, details in results["validation_results"].items():
                status = "✅" if details["passed"] else "❌"
                found = ", ".join(details["found"]) or "None"
                table.add_row(category, status, found)
                
        # Print results to console
        self.console.print(table)
        
        # Log to file
        log_message = (
            f"QA Validation: {results['status']} "
            f"(Pass Rate: {results['pass_rate']:.1f}%) "
            f"File: {results['file']}"
        )
        self.logger.info(log_message)
        
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare QA tasks."""
        if task.task_type not in ["qa.frontend_validation", "qa.backend_validation"]:
            raise ValueError(f"Unsupported task type: {task.task_type}")
        return task 