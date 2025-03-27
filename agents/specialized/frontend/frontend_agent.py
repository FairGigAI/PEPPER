"""Frontend agent for handling frontend development tasks."""

import os
import time
from typing import Dict, Any, Optional
from loguru import logger
from core.agent_base import BaseAgent, Task
from core.config_models import FrontendAgentConfig
from core.exceptions import FatalError
from core.config_validator import ConfigurationValidator

class FrontendAgent(BaseAgent):
    """Agent responsible for frontend development tasks."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        if not isinstance(self.config, FrontendAgentConfig):
            raise FatalError(f"Invalid configuration for FrontendAgent {agent_id}")
            
        self.output_dir = self.config.component_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.validator = ConfigurationValidator(self.config_dir)
        self.current_throttle = self.config.build_throttle
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing frontend task: {task.task_id}")
        
        # Validate framework
        framework = task.metadata.get("framework", self.config.default_framework)
        if framework not in self.config.supported_frameworks:
            raise FatalError(f"Unsupported framework: {framework}")
            
        # Create validation checkpoint if required
        if self.config.requires_approval:
            checkpoint_id = self.validator.create_checkpoint(
                self.agent_id,
                task.task_id,
                self.config.validation_rules
            )
            task.metadata["checkpoint_id"] = checkpoint_id
            
        return {
            "framework": framework,
            "styling": task.metadata.get("styling", self.config.metadata.get("default_styling")),
            "component_template": self.config.metadata.get("component_template", "functional")
        }
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the frontend task."""
        logger.info(f"Executing frontend task: {task.task_id}")
        
        # Check for approval if required
        if self.config.requires_approval:
            checkpoint_id = task.metadata.get("checkpoint_id")
            if not checkpoint_id:
                raise FatalError("Missing checkpoint ID for task requiring approval")
                
            status = self.validator.get_checkpoint_status(checkpoint_id)
            if status != "approved":
                raise FatalError(f"Task not approved. Current status: {status}")
        
        # Apply throttle delay
        if self.current_throttle != 1.0:
            delay = (1.0 / self.current_throttle) - 1.0
            logger.info(f"Applying throttle delay: {delay:.2f}s")
            time.sleep(delay)
        
        if task.task_type == "frontend.component_creation":
            return await self._create_react_component(task)
        else:
            raise FatalError(f"Unsupported task type: {task.task_type}")
            
    def set_throttle(self, throttle: float):
        """Set the build throttle speed."""
        if not 0.1 <= throttle <= 2.0:
            raise ValueError("Throttle must be between 0.1 and 2.0")
        self.current_throttle = throttle
        logger.info(f"Build throttle set to: {throttle}")
        
    async def _create_react_component(self, task: Task) -> Dict[str, Any]:
        """Create a new React component."""
        # Extract component name from metadata or description
        component_name = task.metadata.get("component_name") or task.description.split()[-1].capitalize()
        file_name = f"{component_name}.tsx"
        file_path = os.path.join(self.output_dir, file_name)
        
        # Validate component size limits
        if self.config.validation_rules.get("max_component_size"):
            # Estimate component size based on props and template
            estimated_size = len(task.metadata.get("props", [])) * 2 + 20  # Rough estimate
            if estimated_size > self.config.validation_rules["max_component_size"]:
                raise FatalError(f"Component size exceeds limit: {estimated_size} > {self.config.validation_rules['max_component_size']}")
        
        # Generate component code based on template
        template = task.metadata.get("component_template", "functional")
        if template == "functional":
            component_code = self._generate_functional_component(component_name, task.metadata)
        else:
            component_code = self._generate_class_component(component_name, task.metadata)
        
        # Generate CSS file
        css_code = self._generate_css(component_name, task.metadata)
        
        # Validate CSS size
        if self.config.validation_rules.get("max_css_size"):
            css_lines = len(css_code.splitlines())
            if css_lines > self.config.validation_rules["max_css_size"]:
                raise FatalError(f"CSS size exceeds limit: {css_lines} > {self.config.validation_rules['max_css_size']}")
        
        # Write files
        try:
            with open(file_path, 'w') as f:
                f.write(component_code)
            logger.info(f"Created React component: {file_path}")
            
            css_path = os.path.join(self.output_dir, f"{component_name}.css")
            with open(css_path, 'w') as f:
                f.write(css_code)
            logger.info(f"Created CSS file: {css_path}")
            
            return {
                "status": "success",
                "message": f"Created React component {component_name}",
                "details": {
                    "component_file": file_path,
                    "css_file": css_path,
                    "component_name": component_name,
                    "framework": task.metadata.get("framework"),
                    "template": template
                }
            }
        except Exception as e:
            logger.error(f"Failed to create component: {e}")
            raise
            
    def _generate_functional_component(self, component_name: str, metadata: Dict[str, Any]) -> str:
        """Generate a functional React component."""
        props = metadata.get("props", [])
        props_interface = "\n".join(f"    {prop}: any;" for prop in props)
        
        return f"""import React from 'react';
import './{component_name}.css';

interface {component_name}Props {{
{props_interface}
}}

export const {component_name}: React.FC<{component_name}Props> = ({', '.join(props)}) => {{
    return (
        <div className="{component_name.lower()}-container">
            <h1>{component_name}</h1>
            {{/* Add component content here */}}
        </div>
    );
}};
"""
        
    def _generate_class_component(self, component_name: str, metadata: Dict[str, Any]) -> str:
        """Generate a class-based React component."""
        props = metadata.get("props", [])
        props_interface = "\n".join(f"    {prop}: any;" for prop in props)
        
        return f"""import React from 'react';
import './{component_name}.css';

interface {component_name}Props {{
{props_interface}
}}

interface {component_name}State {{
    // Add state properties here
}}

export class {component_name} extends React.Component<{component_name}Props, {component_name}State> {{
    constructor(props: {component_name}Props) {{
        super(props);
        this.state = {{
            // Initialize state here
        }};
    }}
    
    render() {{
        return (
            <div className="{component_name.lower()}-container">
                <h1>{component_name}</h1>
                {{/* Add component content here */}}
            </div>
        );
    }}
}}
"""
        
    def _generate_css(self, component_name: str, metadata: Dict[str, Any]) -> str:
        """Generate CSS for the component."""
        styling = metadata.get("styling", "default")
        
        if styling == "tailwind":
            return f"""/* Tailwind classes will be used instead of CSS */
.{component_name.lower()}-container {{
    @apply p-4 m-4 rounded-lg shadow-md;
}}
"""
        else:
            return f""".{component_name.lower()}-container {{
    padding: 1rem;
    margin: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}}
"""
        
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing frontend task: {task.task_id}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "framework": task.metadata.get("framework"),
            "styling": task.metadata.get("styling"),
            "template": task.metadata.get("component_template")
        }
        
        return result
            
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare frontend tasks."""
        if "framework" in task.metadata:
            if task.metadata["framework"] not in self.supported_frameworks:
                raise ValueError(f"Unsupported framework: {task.metadata['framework']}")
        return task 