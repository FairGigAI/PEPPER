"""Validator for React components."""

import os
from typing import Dict, Any
from loguru import logger

def validate_component(path: str) -> Dict[str, Any]:
    """
    Validate a React component file.
    
    Args:
        path: Path to the React component file
        
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
            
        # Check for component name (should match filename)
        component_name = os.path.splitext(os.path.basename(path))[0]
        if component_name not in content:
            return {
                "status": "FAIL",
                "reason": f"Component name '{component_name}' not found in file"
            }
            
        # Check for export default
        if "export default" not in content and "export const" not in content:
            return {
                "status": "FAIL",
                "reason": "No export statement found"
            }
            
        # Check for JSX tags
        if "<" not in content or ">" not in content:
            return {
                "status": "FAIL",
                "reason": "No JSX tags found"
            }
            
        return {
            "status": "PASS",
            "reason": "Component validation successful",
            "details": {
                "component_name": component_name,
                "has_export": True,
                "has_jsx": True
            }
        }
        
    except Exception as e:
        return {
            "status": "FAIL",
            "reason": f"Error reading file: {str(e)}"
        } 