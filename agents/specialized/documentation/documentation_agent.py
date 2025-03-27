"""Documentation Agent for generating and managing project documentation."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from loguru import logger
from rich.console import Console
from rich.table import Table

from core.agent import Agent
from core.config_models import DocumentationAgentConfig
from core.exceptions import FatalError

class DocumentationAgent(Agent):
    """Agent responsible for generating and managing project documentation."""
    
    def __init__(self, agent_id: str, config: DocumentationAgentConfig):
        """Initialize the DocumentationAgent.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration for the documentation agent
        """
        super().__init__(agent_id, config)
        self.output_dir = config.output_dir
        self.templates_dir = config.templates_dir
        self.supported_doc_types = config.supported_doc_types
        self.validation_rules = config.validation_rules
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True
        )
        
        # Create necessary directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize markdown converter
        self.md_converter = markdown.Markdown(extensions=['tables', 'fenced_code'])
        
        self.console = Console()
        
    async def preprocess(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess the task to validate inputs and prepare for execution.
        
        Args:
            task: Task to preprocess
            
        Returns:
            Dict containing preprocessed task data
            
        Raises:
            FatalError: If task validation fails
        """
        # Validate doc_type
        doc_type = task.get("metadata", {}).get("doc_type")
        if doc_type not in self.supported_doc_types:
            raise FatalError(f"Unsupported document type: {doc_type}")
            
        # Validate template if specified
        template = task.get("metadata", {}).get("template")
        if template:
            try:
                self.env.get_template(f"{template}.md")
            except TemplateNotFound:
                raise FatalError(f"Template not found: {template}")
                
        return task
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the documentation task.
        
        Args:
            task: Task to execute
            
        Returns:
            Dict containing execution results
        """
        task_type = task.get("task_type", "")
        
        if task_type == "documentation.generate":
            return await self._generate_documentation(task)
        elif task_type == "documentation.update":
            return await self._update_documentation(task)
        elif task_type == "documentation.review":
            return await self._review_documentation(task)
        elif task_type == "documentation.validate":
            return await self._validate_documentation(task)
        else:
            raise FatalError(f"Unsupported task type: {task_type}")
            
    async def _generate_documentation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new documentation.
        
        Args:
            task: Task containing documentation generation parameters
            
        Returns:
            Dict containing generation results
        """
        metadata = task.get("metadata", {})
        doc_type = metadata.get("doc_type")
        template = metadata.get("template", "default")
        content = metadata.get("content", {})
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{metadata.get('title', 'document')}_{timestamp}.{doc_type}"
        output_path = Path(self.output_dir) / filename
        
        # Load and render template
        template_obj = self.env.get_template(f"{template}.md")
        rendered_content = template_obj.render(**content)
        
        # Convert to HTML if needed
        if doc_type == "html":
            rendered_content = self.md_converter.convert(rendered_content)
            
        # Write to file
        output_path.write_text(rendered_content)
        
        return {
            "status": "success",
            "output_file": str(output_path),
            "doc_type": doc_type
        }
        
    async def _update_documentation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing documentation.
        
        Args:
            task: Task containing documentation update parameters
            
        Returns:
            Dict containing update results
        """
        metadata = task.get("metadata", {})
        file_path = metadata.get("file_path")
        updates = metadata.get("updates", {})
        
        if not file_path or not Path(file_path).exists():
            raise FatalError(f"Document not found: {file_path}")
            
        # Read existing content
        content = Path(file_path).read_text()
        
        # Apply updates
        for section, new_content in updates.items():
            # Simple section replacement - could be enhanced with more sophisticated parsing
            section_start = f"## {section}"
            section_end = "##"
            
            start_idx = content.find(section_start)
            if start_idx != -1:
                end_idx = content.find(section_end, start_idx + len(section_start))
                if end_idx == -1:
                    end_idx = len(content)
                    
                updated_section = f"{section_start}\n\n{new_content}\n\n"
                content = content[:start_idx] + updated_section + content[end_idx:]
                
        # Write updated content
        Path(file_path).write_text(content)
        
        return {
            "status": "success",
            "file_path": file_path
        }
        
    async def _review_documentation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Review documentation for quality and completeness.
        
        Args:
            task: Task containing documentation review parameters
            
        Returns:
            Dict containing review results
        """
        metadata = task.get("metadata", {})
        file_path = metadata.get("file_path")
        criteria = metadata.get("review_criteria", ["completeness", "clarity", "formatting"])
        
        if not file_path or not Path(file_path).exists():
            raise FatalError(f"Document not found: {file_path}")
            
        # Read content
        content = Path(file_path).read_text()
        
        # Perform review
        review_results = {
            "completeness": self._check_completeness(content),
            "clarity": self._check_clarity(content),
            "formatting": self._check_formatting(content),
            "suggestions": []
        }
        
        # Generate suggestions
        if review_results["completeness"]["score"] < 0.8:
            review_results["suggestions"].append("Consider adding more detailed examples")
        if review_results["clarity"]["score"] < 0.8:
            review_results["suggestions"].append("Some sections could be clearer")
        if review_results["formatting"]["score"] < 0.8:
            review_results["suggestions"].append("Check markdown formatting")
            
        return {
            "status": "success",
            "review_results": review_results
        }
        
    async def _validate_documentation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate documentation against rules and check cross-references.
        
        Args:
            task: Task containing documentation validation parameters
            
        Returns:
            Dict containing validation results
        """
        metadata = task.get("metadata", {})
        files = metadata.get("files", [])
        check_cross_references = metadata.get("check_cross_references", False)
        
        validation_results = {
            "files_validated": [],
            "cross_references": {},
            "errors": []
        }
        
        for file_path in files:
            if not Path(file_path).exists():
                validation_results["errors"].append(f"File not found: {file_path}")
                continue
                
            # Validate file
            content = Path(file_path).read_text()
            file_validation = self._validate_file(content, self.validation_rules)
            validation_results["files_validated"].append({
                "file": file_path,
                "valid": file_validation["valid"],
                "issues": file_validation["issues"]
            })
            
            # Check cross-references if requested
            if check_cross_references:
                refs = self._find_cross_references(content)
                validation_results["cross_references"][file_path] = refs
                
        return {
            "status": "success",
            "validation_results": validation_results
        }
        
    def _check_completeness(self, content: str) -> Dict[str, Any]:
        """Check documentation completeness.
        
        Args:
            content: Documentation content
            
        Returns:
            Dict containing completeness check results
        """
        required_sections = ["Overview", "Usage", "Configuration"]
        score = 0.0
        
        for section in required_sections:
            if f"## {section}" in content:
                score += 1.0
                
        return {
            "score": score / len(required_sections),
            "missing_sections": [s for s in required_sections if f"## {s}" not in content]
        }
        
    def _check_clarity(self, content: str) -> Dict[str, Any]:
        """Check documentation clarity.
        
        Args:
            content: Documentation content
            
        Returns:
            Dict containing clarity check results
        """
        # Simple clarity checks - could be enhanced with NLP
        issues = []
        
        # Check for long paragraphs
        paragraphs = content.split("\n\n")
        for p in paragraphs:
            if len(p.split()) > 100:
                issues.append("Long paragraph detected")
                
        # Check for technical terms without explanation
        technical_terms = ["API", "endpoint", "configuration", "parameter"]
        for term in technical_terms:
            if term in content and f"**{term}**" not in content:
                issues.append(f"Technical term '{term}' used without explanation")
                
        return {
            "score": 1.0 - (len(issues) * 0.1),
            "issues": issues
        }
        
    def _check_formatting(self, content: str) -> Dict[str, Any]:
        """Check documentation formatting.
        
        Args:
            content: Documentation content
            
        Returns:
            Dict containing formatting check results
        """
        issues = []
        
        # Check for proper heading hierarchy
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("#"):
                if i > 0 and lines[i-1].strip() != "":
                    issues.append("Headings should be preceded by blank line")
                    
        # Check for consistent list formatting
        if "- " in content and "* " in content:
            issues.append("Inconsistent list markers used")
            
        return {
            "score": 1.0 - (len(issues) * 0.1),
            "issues": issues
        }
        
    def _validate_file(self, content: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a file against documentation rules.
        
        Args:
            content: File content
            rules: Validation rules
            
        Returns:
            Dict containing validation results
        """
        issues = []
        
        # Check required sections
        for section in rules.get("required_sections", []):
            if f"## {section}" not in content:
                issues.append(f"Missing required section: {section}")
                
        # Check minimum content length
        min_length = rules.get("min_content_length", 100)
        if len(content.split()) < min_length:
            issues.append(f"Content too short (minimum {min_length} words)")
            
        # Check for code blocks
        if rules.get("require_code_examples", False) and "```" not in content:
            issues.append("Missing code examples")
            
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
        
    def _find_cross_references(self, content: str) -> Dict[str, Any]:
        """Find cross-references in documentation.
        
        Args:
            content: Documentation content
            
        Returns:
            Dict containing cross-reference information
        """
        import re
        
        # Find markdown links
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        
        return {
            "links": [
                {
                    "text": text,
                    "target": target,
                    "valid": Path(target).exists()
                }
                for text, target in links
            ]
        }
        
    async def postprocess(self, task: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing documentation task: {task.get('task_id')}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "doc_type": task.get("metadata", {}).get("doc_type"),
            "template": task.get("metadata", {}).get("template"),
            "output_format": task.get("metadata", {}).get("output_format")
        }
        
        return result
            
    async def preprocess_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and prepare documentation tasks."""
        if "doc_type" in task.get("metadata", {}):
            if task.get("metadata", {})["doc_type"] not in self.supported_doc_types:
                raise ValueError(f"Unsupported documentation type: {task.get('metadata', {})['doc_type']}")
        return task 