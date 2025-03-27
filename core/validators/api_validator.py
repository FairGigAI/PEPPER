"""Validator for FastAPI endpoints."""

import os
from typing import Dict, Any
from loguru import logger

def validate_endpoint(path: str) -> Dict[str, Any]:
    """
    Validate a FastAPI endpoint file.
    
    Args:
        path: Path to the FastAPI endpoint file
        
    Returns:
        Dict containing validation status and details
    """
    if not os.path.exists(path):
        return {
            "status": "FAIL",
            "reason": f"File not found: {path}"
        }
        
    try:
        with open(path, 'r') as f:
            content = f.read()
            
        # Check for required imports
        required_imports = ["fastapi", "APIRouter", "pydantic"]
        missing_imports = [imp for imp in required_imports if imp not in content]
        if missing_imports:
            return {
                "status": "FAIL",
                "reason": f"Missing required imports: {', '.join(missing_imports)}"
            }
            
        # Check for router definition
        if "router = APIRouter" not in content:
            return {
                "status": "FAIL",
                "reason": "No APIRouter definition found"
            }
            
        # Check for route decorators
        if "@router." not in content:
            return {
                "status": "FAIL",
                "reason": "No route decorators found"
            }
            
        # Check for return statements
        if "return" not in content:
            return {
                "status": "FAIL",
                "reason": "No return statements found"
            }
            
        return {
            "status": "PASS",
            "reason": "Endpoint validation successful",
            "details": {
                "has_imports": True,
                "has_router": True,
                "has_routes": True,
                "has_returns": True
            }
        }
        
    except Exception as e:
        return {
            "status": "FAIL",
            "reason": f"Error reading file: {str(e)}"
        } 