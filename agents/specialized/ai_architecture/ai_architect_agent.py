"""AI Architect agent for planning system structure and suggesting agent strategies."""

import os
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.table import Table

from core.agent_base import BaseAgent, Task
from core.config_models import AIArchitectAgentConfig
from core.exceptions import FatalError
from core.agent_orchestrator import TaskDependency

class AIArchitectAgent(BaseAgent):
    """Agent responsible for planning system architecture and suggesting agent strategies."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        if not isinstance(self.config, AIArchitectAgentConfig):
            raise FatalError(f"Invalid configuration for AIArchitectAgent {agent_id}")
            
        self.console = Console()
        self.output_dir = self.config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing AI architect task: {task.task_id}")
        
        # Validate architecture type
        arch_type = task.metadata.get("architecture_type", "microservices")
        if arch_type not in self.config.supported_architectures:
            raise FatalError(f"Unsupported architecture type: {arch_type}")
            
        return {
            "architecture_type": arch_type,
            "scale_factor": task.metadata.get("scale_factor", "medium"),
            "deployment_type": task.metadata.get("deployment_type", "cloud")
        }
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the AI architect task."""
        logger.info(f"Executing AI architect task: {task.task_id}")
        
        # Get project requirements
        requirements = task.metadata.get("requirements", {})
        
        # Analyze requirements and generate architecture plan
        architecture_plan = self._generate_architecture_plan(requirements, task.metadata)
        
        # Generate agent strategies
        agent_strategies = self._generate_agent_strategies(architecture_plan, task.metadata)
        
        # Save architecture documentation
        output_file = f"architecture_{task.task_id.lower()}.md"
        output_path = os.path.join(self.output_dir, output_file)
        
        try:
            self._save_architecture_docs(architecture_plan, agent_strategies, output_path)
            logger.info(f"Generated architecture documentation: {output_path}")
            
            return {
                "status": "success",
                "message": "Generated architecture plan and agent strategies",
                "details": {
                    "output_file": output_file,
                    "architecture_type": task.metadata.get("architecture_type"),
                    "component_count": len(architecture_plan.get("components", [])),
                    "strategy_count": len(agent_strategies)
                }
            }
        except Exception as e:
            logger.error(f"Failed to generate architecture plan: {e}")
            raise
            
    def _generate_architecture_plan(self, requirements: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system architecture plan based on requirements."""
        arch_type = metadata.get("architecture_type", "microservices")
        scale_factor = metadata.get("scale_factor", "medium")
        
        # Define base architecture components
        components = []
        
        if arch_type == "microservices":
            components = self._generate_microservices_architecture(requirements, scale_factor)
        elif arch_type == "monolithic":
            components = self._generate_monolithic_architecture(requirements, scale_factor)
        elif arch_type == "serverless":
            components = self._generate_serverless_architecture(requirements, scale_factor)
            
        # Generate deployment configuration
        deployment = self._generate_deployment_config(metadata.get("deployment_type", "cloud"))
        
        return {
            "architecture_type": arch_type,
            "scale_factor": scale_factor,
            "components": components,
            "deployment": deployment,
            "requirements": requirements
        }
        
    def _generate_microservices_architecture(self, requirements: Dict[str, Any], scale_factor: str) -> List[Dict[str, Any]]:
        """Generate microservices architecture components."""
        components = []
        
        # Extract service requirements
        services = requirements.get("services", [])
        
        for service in services:
            component = {
                "name": service.get("name", "unnamed_service"),
                "type": "microservice",
                "description": service.get("description", ""),
                "dependencies": service.get("dependencies", []),
                "scale": self._calculate_service_scale(service, scale_factor),
                "resources": self._calculate_service_resources(service, scale_factor)
            }
            components.append(component)
            
        # Add shared components
        shared_components = [
            {
                "name": "api_gateway",
                "type": "gateway",
                "description": "API Gateway for service routing",
                "dependencies": [],
                "scale": "high",
                "resources": {"cpu": "2", "memory": "4Gi"}
            },
            {
                "name": "service_discovery",
                "type": "discovery",
                "description": "Service discovery and registration",
                "dependencies": [],
                "scale": "high",
                "resources": {"cpu": "2", "memory": "4Gi"}
            }
        ]
        components.extend(shared_components)
        
        return components
        
    def _generate_monolithic_architecture(self, requirements: Dict[str, Any], scale_factor: str) -> List[Dict[str, Any]]:
        """Generate monolithic architecture components."""
        components = []
        
        # Create main application component
        main_component = {
            "name": "main_application",
            "type": "monolith",
            "description": "Main application server",
            "dependencies": [],
            "scale": scale_factor,
            "resources": self._calculate_monolith_resources(requirements, scale_factor)
        }
        components.append(main_component)
        
        # Add database component
        db_component = {
            "name": "database",
            "type": "database",
            "description": "Main application database",
            "dependencies": [],
            "scale": scale_factor,
            "resources": {"cpu": "4", "memory": "8Gi"}
        }
        components.append(db_component)
        
        return components
        
    def _generate_serverless_architecture(self, requirements: Dict[str, Any], scale_factor: str) -> List[Dict[str, Any]]:
        """Generate serverless architecture components."""
        components = []
        
        # Extract function requirements
        functions = requirements.get("functions", [])
        
        for func in functions:
            component = {
                "name": func.get("name", "unnamed_function"),
                "type": "function",
                "description": func.get("description", ""),
                "dependencies": func.get("dependencies", []),
                "runtime": func.get("runtime", "python"),
                "memory": func.get("memory", "256MB"),
                "timeout": func.get("timeout", "30s")
            }
            components.append(component)
            
        # Add shared components
        shared_components = [
            {
                "name": "api_gateway",
                "type": "gateway",
                "description": "API Gateway for function routing",
                "dependencies": [],
                "scale": "high"
            }
        ]
        components.extend(shared_components)
        
        return components
        
    def _generate_deployment_config(self, deployment_type: str) -> Dict[str, Any]:
        """Generate deployment configuration."""
        if deployment_type == "cloud":
            return {
                "type": "cloud",
                "provider": "aws",
                "regions": ["us-east-1", "us-west-2"],
                "auto_scaling": True,
                "load_balancing": True
            }
        elif deployment_type == "on_premise":
            return {
                "type": "on_premise",
                "auto_scaling": False,
                "load_balancing": True
            }
        else:
            return {
                "type": "hybrid",
                "cloud_provider": "aws",
                "on_premise": True,
                "auto_scaling": True,
                "load_balancing": True
            }
            
    def _generate_agent_strategies(self, architecture_plan: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate agent strategies based on architecture plan."""
        strategies = []
        
        # Generate strategies for each component
        for component in architecture_plan.get("components", []):
            component_strategies = self._generate_component_strategies(component, metadata)
            strategies.extend(component_strategies)
            
        # Add system-wide strategies
        system_strategies = self._generate_system_strategies(architecture_plan, metadata)
        strategies.extend(system_strategies)
        
        return strategies
        
    def _generate_component_strategies(self, component: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategies for a specific component."""
        strategies = []
        component_type = component.get("type", "")
        
        if component_type == "microservice":
            strategies.extend([
                {
                    "agent": "frontend_agent",
                    "strategy": "component_based_development",
                    "priority": "high",
                    "description": f"Develop frontend components for {component['name']}"
                },
                {
                    "agent": "backend_agent",
                    "strategy": "api_first_development",
                    "priority": "high",
                    "description": f"Develop backend API for {component['name']}"
                },
                {
                    "agent": "qa_agent",
                    "strategy": "microservice_testing",
                    "priority": "medium",
                    "description": f"Test {component['name']} microservice"
                }
            ])
        elif component_type == "monolith":
            strategies.extend([
                {
                    "agent": "frontend_agent",
                    "strategy": "monolithic_development",
                    "priority": "high",
                    "description": "Develop frontend for monolithic application"
                },
                {
                    "agent": "backend_agent",
                    "strategy": "monolithic_backend",
                    "priority": "high",
                    "description": "Develop backend for monolithic application"
                },
                {
                    "agent": "qa_agent",
                    "strategy": "monolithic_testing",
                    "priority": "medium",
                    "description": "Test monolithic application"
                }
            ])
        elif component_type == "function":
            strategies.extend([
                {
                    "agent": "backend_agent",
                    "strategy": "serverless_development",
                    "priority": "high",
                    "description": f"Develop serverless function {component['name']}"
                },
                {
                    "agent": "qa_agent",
                    "strategy": "function_testing",
                    "priority": "medium",
                    "description": f"Test serverless function {component['name']}"
                }
            ])
            
        return strategies
        
    def _generate_system_strategies(self, architecture_plan: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate system-wide strategies."""
        return [
            {
                "agent": "infra_agent",
                "strategy": "infrastructure_as_code",
                "priority": "high",
                "description": "Set up infrastructure using IaC"
            },
            {
                "agent": "security_agent",
                "strategy": "security_audit",
                "priority": "high",
                "description": "Perform security audit"
            },
            {
                "agent": "documentation_agent",
                "strategy": "architecture_documentation",
                "priority": "medium",
                "description": "Generate architecture documentation"
            }
        ]
        
    def _calculate_service_scale(self, service: Dict[str, Any], scale_factor: str) -> str:
        """Calculate service scale based on requirements and scale factor."""
        if scale_factor == "small":
            return "low"
        elif scale_factor == "medium":
            return "medium"
        else:
            return "high"
            
    def _calculate_service_resources(self, service: Dict[str, Any], scale_factor: str) -> Dict[str, str]:
        """Calculate service resource requirements."""
        if scale_factor == "small":
            return {"cpu": "0.5", "memory": "1Gi"}
        elif scale_factor == "medium":
            return {"cpu": "1", "memory": "2Gi"}
        else:
            return {"cpu": "2", "memory": "4Gi"}
            
    def _calculate_monolith_resources(self, requirements: Dict[str, Any], scale_factor: str) -> Dict[str, str]:
        """Calculate monolithic application resource requirements."""
        if scale_factor == "small":
            return {"cpu": "2", "memory": "4Gi"}
        elif scale_factor == "medium":
            return {"cpu": "4", "memory": "8Gi"}
        else:
            return {"cpu": "8", "memory": "16Gi"}
            
    def _save_architecture_docs(self, architecture_plan: Dict[str, Any], agent_strategies: List[Dict[str, Any]], output_path: str):
        """Save architecture documentation to markdown file."""
        with open(output_path, 'w') as f:
            f.write(f"""# System Architecture Plan

## Overview
This document outlines the system architecture and agent strategies for the project.

## Architecture Type
{architecture_plan['architecture_type']}

## Scale Factor
{architecture_plan['scale_factor']}

## Components

""")
            
            for component in architecture_plan["components"]:
                f.write(f"""### {component['name']}
**Type:** {component['type']}
**Description:** {component['description']}

**Dependencies:**
{', '.join(component['dependencies']) if component['dependencies'] else 'None'}

**Scale:** {component['scale']}
**Resources:** {component.get('resources', 'N/A')}

""")
                
            f.write("""## Deployment Configuration

""")
            for key, value in architecture_plan["deployment"].items():
                f.write(f"- **{key}:** {value}\n")
                
            f.write("""\n## Agent Strategies

""")
            for strategy in agent_strategies:
                f.write(f"""### {strategy['agent']}
**Strategy:** {strategy['strategy']}
**Priority:** {strategy['priority']}
**Description:** {strategy['description']}

""")
                
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing AI architect task: {task.task_id}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "architecture_type": task.metadata.get("architecture_type"),
            "scale_factor": task.metadata.get("scale_factor"),
            "deployment_type": task.metadata.get("deployment_type")
        }
        
        return result
            
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare AI architect tasks."""
        if "requirements" not in task.metadata:
            raise ValueError("Project requirements must be specified in task metadata")
        return task 