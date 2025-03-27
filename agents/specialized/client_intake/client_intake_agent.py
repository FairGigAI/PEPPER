"""Client Intake agent for processing client requirements and converting them into tasks."""

import os
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.table import Table
import json

from core.agent_base import BaseAgent, Task
from core.config_models import ClientIntakeAgentConfig
from core.exceptions import FatalError
from core.agent_orchestrator import TaskDependency
from core.feedback_system import FeedbackSystem, TaskCompletion

class ClientIntakeAgent(BaseAgent):
    """Agent responsible for processing client requirements and converting them into tasks."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        if not isinstance(self.config, ClientIntakeAgentConfig):
            raise FatalError(f"Invalid configuration for ClientIntakeAgent {agent_id}")
            
        self.console = Console()
        self.input_dir = self.config.input_dir
        self.output_dir = self.config.output_dir
        self.feedback_system = FeedbackSystem(self.llm_interface, self.slack_bot)
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def initialize(self):
        """Initialize the agent."""
        await super().initialize()
        await self.feedback_system.initialize()
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing client intake task: {task.task_id}")
        
        # Validate input format
        input_format = task.metadata.get("input_format", "markdown")
        if input_format not in self.config.supported_input_formats:
            raise FatalError(f"Unsupported input format: {input_format}")
            
        # Get historical metrics for better estimation
        historical_metrics = await self._get_historical_metrics()
            
        return {
            "input_format": input_format,
            "output_format": task.metadata.get("output_format", "yaml"),
            "project_type": task.metadata.get("project_type", "web"),
            "historical_metrics": historical_metrics
        }
        
    async def _get_historical_metrics(self) -> Dict[str, Any]:
        """Get historical metrics for better estimation."""
        try:
            metrics_file = self.feedback_system.data_dir / "agent_metrics_client_intake.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load historical metrics: {e}")
            return {}
            
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the client intake task."""
        logger.info(f"Executing client intake task: {task.task_id}")
        
        start_time = datetime.now()
        
        try:
            # Get input file path
            input_file = task.metadata.get("input_file")
            if not input_file:
                raise FatalError("No input file specified")
                
            input_path = os.path.join(self.input_dir, input_file)
            if not os.path.exists(input_path):
                raise FatalError(f"Input file not found: {input_path}")
                
            # Process the input file
            content = self._read_input_file(input_path, task.metadata.get("input_format"))
            
            # Analyze content and generate tasks
            tasks = self._analyze_content(content, task.metadata)
            
            # Save task dependencies
            output_file = f"tasks_{task.task_id.lower()}.yaml"
            output_path = os.path.join(self.output_dir, output_file)
            
            self._save_task_dependencies(tasks, output_path)
            logger.info(f"Generated task dependencies: {output_path}")
            
            # Record task completion
            completion = TaskCompletion(
                task_id=task.task_id,
                agent_id=self.agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                complexity=task.metadata.get("complexity", 5),
                dependencies=task.metadata.get("dependencies", []),
                success=True,
                notes="Successfully generated task dependencies"
            )
            
            await self.feedback_system.record_task_completion(completion)
            
            return {
                "status": "success",
                "message": f"Generated {len(tasks)} task dependencies",
                "details": {
                    "input_file": input_file,
                    "output_file": output_file,
                    "task_count": len(tasks),
                    "project_type": task.metadata.get("project_type")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate task dependencies: {e}")
            
            # Record failed task completion
            completion = TaskCompletion(
                task_id=task.task_id,
                agent_id=self.agent_id,
                estimated_duration=task.metadata.get("estimated_duration", 0),
                actual_duration=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                complexity=task.metadata.get("complexity", 5),
                dependencies=task.metadata.get("dependencies", []),
                success=False,
                notes=f"Failed: {str(e)}"
            )
            
            await self.feedback_system.record_task_completion(completion)
            raise
            
    def _read_input_file(self, file_path: str, format: str) -> str:
        """Read input file in specified format."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if format == "markdown":
                return content
            elif format == "pdf":
                # TODO: Implement PDF parsing
                raise NotImplementedError("PDF parsing not yet implemented")
            elif format == "docx":
                # TODO: Implement DOCX parsing
                raise NotImplementedError("DOCX parsing not yet implemented")
            else:
                raise FatalError(f"Unsupported input format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to read input file: {e}")
            raise
            
    def _analyze_content(self, content: str, metadata: Dict[str, Any]) -> List[TaskDependency]:
        """Analyze content and generate task dependencies."""
        tasks = []
        project_type = metadata.get("project_type", "web")
        
        # Split content into sections
        sections = self._split_into_sections(content)
        
        # Process each section
        for section in sections:
            section_tasks = self._process_section(section, project_type)
            tasks.extend(section_tasks)
            
        # Add dependencies between tasks
        self._add_task_dependencies(tasks)
        
        return tasks
        
    def _split_into_sections(self, content: str) -> List[Dict[str, Any]]:
        """Split content into logical sections."""
        sections = []
        current_section = {"title": "", "content": "", "type": "unknown"}
        
        for line in content.split("\n"):
            if line.startswith("# "):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "title": line[2:].strip(),
                    "content": "",
                    "type": self._determine_section_type(line[2:].strip())
                }
            else:
                current_section["content"] += line + "\n"
                
        if current_section["content"]:
            sections.append(current_section)
            
        return sections
        
    def _determine_section_type(self, title: str) -> str:
        """Determine the type of section based on its title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["frontend", "ui", "interface", "design"]):
            return "frontend"
        elif any(word in title_lower for word in ["backend", "api", "server", "database"]):
            return "backend"
        elif any(word in title_lower for word in ["test", "qa", "validation", "verify"]):
            return "qa"
        elif any(word in title_lower for word in ["infra", "deploy", "cloud", "server"]):
            return "infrastructure"
        elif any(word in title_lower for word in ["security", "auth", "permission"]):
            return "security"
        else:
            return "general"
            
    def _process_section(self, section: Dict[str, Any], project_type: str) -> List[TaskDependency]:
        """Process a section and generate task dependencies."""
        tasks = []
        section_type = section["type"]
        
        # Generate tasks based on section type
        if section_type == "frontend":
            tasks.extend(self._generate_frontend_tasks(section, project_type))
        elif section_type == "backend":
            tasks.extend(self._generate_backend_tasks(section, project_type))
        elif section_type == "qa":
            tasks.extend(self._generate_qa_tasks(section))
        elif section_type == "infrastructure":
            tasks.extend(self._generate_infra_tasks(section))
        elif section_type == "security":
            tasks.extend(self._generate_security_tasks(section))
        else:
            tasks.extend(self._generate_general_tasks(section))
            
        return tasks
        
    def _generate_frontend_tasks(self, section: Dict[str, Any], project_type: str) -> List[TaskDependency]:
        """Generate frontend-related tasks."""
        tasks = []
        content = section["content"]
        
        # Extract component requirements
        components = self._extract_components(content)
        for component in components:
            task = TaskDependency(
                task_id=f"frontend_{len(tasks)}",
                depends_on=[],
                agent_id="frontend_agent",
                task_type="frontend.component_creation",
                description=f"Create {component} component",
                metadata={
                    "component_name": component,
                    "framework": "react",
                    "project_type": project_type
                }
            )
            tasks.append(task)
            
        return tasks
        
    def _generate_backend_tasks(self, section: Dict[str, Any], project_type: str) -> List[TaskDependency]:
        """Generate backend-related tasks."""
        tasks = []
        content = section["content"]
        
        # Extract API requirements
        apis = self._extract_apis(content)
        for api in apis:
            task = TaskDependency(
                task_id=f"backend_{len(tasks)}",
                depends_on=[],
                agent_id="backend_agent",
                task_type="backend.api_creation",
                description=f"Create {api['name']} API endpoint",
                metadata={
                    "endpoint": api["path"],
                    "methods": api["methods"],
                    "framework": "fastapi",
                    "project_type": project_type
                }
            )
            tasks.append(task)
            
        return tasks
        
    def _generate_qa_tasks(self, section: Dict[str, Any]) -> List[TaskDependency]:
        """Generate QA-related tasks."""
        tasks = []
        content = section["content"]
        
        # Extract test requirements
        test_requirements = self._extract_test_requirements(content)
        for req in test_requirements:
            task = TaskDependency(
                task_id=f"qa_{len(tasks)}",
                depends_on=[],
                agent_id="qa_agent",
                task_type="qa.test_creation",
                description=f"Create {req['type']} tests for {req['target']}",
                metadata={
                    "test_type": req["type"],
                    "target": req["target"],
                    "coverage_threshold": 80
                }
            )
            tasks.append(task)
            
        return tasks
        
    def _generate_infra_tasks(self, section: Dict[str, Any]) -> List[TaskDependency]:
        """Generate infrastructure-related tasks."""
        tasks = []
        content = section["content"]
        
        # Extract infrastructure requirements
        infra_reqs = self._extract_infra_requirements(content)
        for req in infra_reqs:
            task = TaskDependency(
                task_id=f"infra_{len(tasks)}",
                depends_on=[],
                agent_id="infra_agent",
                task_type="infra.setup",
                description=f"Set up {req['type']} infrastructure",
                metadata={
                    "infra_type": req["type"],
                    "environment": req.get("environment", "production"),
                    "provider": req.get("provider", "aws")
                }
            )
            tasks.append(task)
            
        return tasks
        
    def _generate_security_tasks(self, section: Dict[str, Any]) -> List[TaskDependency]:
        """Generate security-related tasks."""
        tasks = []
        content = section["content"]
        
        # Extract security requirements
        security_reqs = self._extract_security_requirements(content)
        for req in security_reqs:
            task = TaskDependency(
                task_id=f"security_{len(tasks)}",
                depends_on=[],
                agent_id="security_agent",
                task_type="security.audit",
                description=f"Perform {req['type']} security audit",
                metadata={
                    "audit_type": req["type"],
                    "scope": req.get("scope", "full"),
                    "compliance": req.get("compliance", [])
                }
            )
            tasks.append(task)
            
        return tasks
        
    def _generate_general_tasks(self, section: Dict[str, Any]) -> List[TaskDependency]:
        """Generate general tasks from section content."""
        tasks = []
        content = section["content"]
        
        # Extract general requirements
        requirements = self._extract_requirements(content)
        for req in requirements:
            task = TaskDependency(
                task_id=f"general_{len(tasks)}",
                depends_on=[],
                agent_id="pm_agent",
                task_type="pm.task_planning",
                description=req["description"],
                metadata={
                    "priority": req.get("priority", "MEDIUM"),
                    "category": req.get("category", "general")
                }
            )
            tasks.append(task)
            
        return tasks
        
    def _extract_components(self, content: str) -> List[str]:
        """Extract component requirements from content."""
        # TODO: Implement component extraction logic
        return ["Header", "Footer", "Navigation"]
        
    def _extract_apis(self, content: str) -> List[Dict[str, Any]]:
        """Extract API requirements from content."""
        # TODO: Implement API extraction logic
        return [
            {
                "name": "User Authentication",
                "path": "/api/v1/auth",
                "methods": ["POST", "GET"]
            }
        ]
        
    def _extract_test_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Extract test requirements from content."""
        # TODO: Implement test requirement extraction logic
        return [
            {
                "type": "unit",
                "target": "UserService"
            }
        ]
        
    def _extract_infra_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Extract infrastructure requirements from content."""
        # TODO: Implement infrastructure requirement extraction logic
        return [
            {
                "type": "web_server",
                "environment": "production",
                "provider": "aws"
            }
        ]
        
    def _extract_security_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Extract security requirements from content."""
        # TODO: Implement security requirement extraction logic
        return [
            {
                "type": "vulnerability_scan",
                "scope": "full",
                "compliance": ["OWASP"]
            }
        ]
        
    def _extract_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Extract general requirements from content."""
        # TODO: Implement requirement extraction logic
        return [
            {
                "description": "Set up project repository",
                "priority": "HIGH",
                "category": "setup"
            }
        ]
        
    def _add_task_dependencies(self, tasks: List[TaskDependency]):
        """Add dependencies between tasks based on their types and order."""
        # Frontend tasks depend on backend tasks
        for frontend_task in tasks:
            if frontend_task.agent_id == "frontend_agent":
                for backend_task in tasks:
                    if backend_task.agent_id == "backend_agent":
                        frontend_task.depends_on.append(backend_task.task_id)
                        
        # QA tasks depend on their respective implementation tasks
        for qa_task in tasks:
            if qa_task.agent_id == "qa_agent":
                target = qa_task.metadata.get("target", "")
                for impl_task in tasks:
                    if impl_task.agent_id in ["frontend_agent", "backend_agent"]:
                        if target in impl_task.description:
                            qa_task.depends_on.append(impl_task.task_id)
                            
    def _save_task_dependencies(self, tasks: List[TaskDependency], output_path: str):
        """Save task dependencies to YAML file."""
        import yaml
        
        # Convert tasks to dictionary format
        tasks_dict = []
        for task in tasks:
            task_dict = {
                "id": task.task_id,
                "depends_on": task.depends_on,
                "agent": task.agent_id,
                "task": task.task_type,
                "description": task.description,
                "metadata": task.metadata
            }
            tasks_dict.append(task_dict)
            
        # Save to YAML file
        with open(output_path, 'w') as f:
            yaml.dump({"tasks": tasks_dict}, f, default_flow_style=False)
            
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing client intake task: {task.task_id}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "input_format": task.metadata.get("input_format"),
            "output_format": task.metadata.get("output_format"),
            "project_type": task.metadata.get("project_type")
        }
        
        return result
            
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare client intake tasks."""
        if "input_file" not in task.metadata:
            raise ValueError("Input file must be specified in task metadata")
        return task 