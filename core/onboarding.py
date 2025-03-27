"""Project onboarding and scoping module for P.E.P.P.E.R."""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from pydantic import BaseModel
from core.agent_base import BaseAgent
from core.communication import SecureCommunication
from core.llm_interface import LLMInterface
from core.exceptions import FatalError
import aiohttp
import json
import pandas as pd
from pathlib import Path
import PyPDF2
import docx
import openpyxl
from bs4 import BeautifulSoup
import speech_recognition as sr
from io import BytesIO

class ProjectRequirement(BaseModel):
    """Model for project requirements."""
    category: str
    description: str
    priority: int
    complexity: float  # 1-10 scale
    estimated_duration: float  # in seconds
    dependencies: List[str] = []
    required_agents: List[str] = []

class ProjectScope(BaseModel):
    """Model for project scope."""
    project_name: str
    description: str
    requirements: List[ProjectRequirement]
    total_estimated_duration: float
    milestones: List[Dict[str, Any]]
    required_agents: List[str]
    dependencies: List[str]
    risk_factors: List[str]

class OnboardingManager:
    """Manages project onboarding and scoping process."""
    
    def __init__(self, llm_interface: LLMInterface):
        """Initialize the onboarding manager."""
        self.llm = llm_interface
        self.available_agents = []
        self.project_scope = None
        self.requirements = []
        
    async def initialize(self):
        """Initialize the onboarding process."""
        # Get list of available agents
        self.available_agents = await self._get_available_agents()
        
    async def start_onboarding(self) -> str:
        """Start the onboarding conversation."""
        initial_prompt = """Hi! I'm P.E.P.P.E.R., your AI development assistant. 
        I'm excited to help you build something amazing! 
        What would you like to build today?"""
        
        return initial_prompt
        
    async def process_response(self, user_response: str) -> str:
        """Process user response and determine next steps."""
        # Analyze the response using LLM
        analysis = await self.llm.analyze_text(
            user_response,
            "Determine if this is a complete project description or needs more information."
        )
        
        if analysis.get("needs_more_info"):
            return await self._generate_follow_up_questions(user_response)
        else:
            return await self._start_scoping_process(user_response)
            
    async def _generate_follow_up_questions(self, context: str) -> str:
        """Generate relevant follow-up questions based on context."""
        prompt = f"""Based on the following project description, generate relevant follow-up questions:
        {context}
        
        Focus on:
        1. Technical requirements
        2. User requirements
        3. Integration needs
        4. Security requirements
        5. Performance expectations"""
        
        questions = await self.llm.generate_text(prompt)
        return questions
        
    async def _start_scoping_process(self, project_description: str) -> str:
        """Begin the project scoping process."""
        # Create initial project scope
        self.project_scope = await self._create_project_scope(project_description)
        
        # Analyze requirements
        self.requirements = await self._analyze_requirements(project_description)
        
        # Calculate timeline
        timeline = await self._calculate_timeline()
        
        return self._format_scope_summary(timeline)
        
    async def _create_project_scope(self, description: str) -> ProjectScope:
        """Create initial project scope."""
        prompt = f"""Analyze the following project description and create a detailed scope:
        {description}
        
        Include:
        1. Project name
        2. Key requirements
        3. Technical dependencies
        4. Required agents
        5. Risk factors"""
        
        scope_data = await self.llm.generate_text(prompt)
        return ProjectScope(**json.loads(scope_data))
        
    async def _analyze_requirements(self, description: str) -> List[ProjectRequirement]:
        """Analyze and break down project requirements."""
        prompt = f"""Break down the following project into detailed requirements:
        {description}
        
        For each requirement, specify:
        1. Category
        2. Description
        3. Priority (1-5)
        4. Complexity (1-10)
        5. Estimated duration
        6. Dependencies
        7. Required agents"""
        
        requirements_data = await self.llm.generate_text(prompt)
        return [ProjectRequirement(**req) for req in json.loads(requirements_data)]
        
    async def _calculate_timeline(self) -> Dict[str, Any]:
        """Calculate project timeline based on requirements and agent capabilities."""
        total_duration = sum(req.estimated_duration for req in self.requirements)
        
        # Calculate parallel execution possibilities
        parallel_tasks = await self._identify_parallel_tasks()
        
        # Adjust timeline based on parallel execution
        adjusted_duration = total_duration / len(parallel_tasks) if parallel_tasks else total_duration
        
        return {
            "total_duration": adjusted_duration,
            "parallel_tasks": parallel_tasks,
            "milestones": await self._generate_milestones(adjusted_duration)
        }
        
    async def _identify_parallel_tasks(self) -> List[List[ProjectRequirement]]:
        """Identify tasks that can be executed in parallel."""
        # Group tasks by dependencies
        task_groups = []
        current_group = []
        
        for req in sorted(self.requirements, key=lambda x: len(x.dependencies)):
            if not req.dependencies:
                current_group.append(req)
            else:
                if current_group:
                    task_groups.append(current_group)
                current_group = [req]
                
        if current_group:
            task_groups.append(current_group)
            
        return task_groups
        
    async def _generate_milestones(self, total_duration: float) -> List[Dict[str, Any]]:
        """Generate project milestones."""
        milestones = []
        current_time = 0
        
        for req in self.requirements:
            milestone = {
                "name": f"Complete {req.category}",
                "duration": req.estimated_duration,
                "start_time": current_time,
                "end_time": current_time + req.estimated_duration,
                "dependencies": req.dependencies
            }
            milestones.append(milestone)
            current_time += req.estimated_duration
            
        return milestones
        
    def _format_scope_summary(self, timeline: Dict[str, Any]) -> str:
        """Format the project scope summary."""
        duration = timeline["total_duration"]
        duration_str = self._format_duration(duration)
        
        summary = f"""Your project sounds very exciting! I've analyzed the requirements and here's what I've found:

1. Project Scope:
   - {self.project_scope.description}
   - {len(self.requirements)} major components identified
   - {len(timeline['parallel_tasks'])} parallel execution streams

2. Timeline:
   - Estimated completion time: {duration_str}
   - This is based on P.E.P.P.E.R.'s 24/7 operation at full capacity
   - Parallel execution of independent components

3. Key Milestones:
"""
        for milestone in timeline["milestones"]:
            milestone_duration = self._format_duration(milestone["duration"])
            summary += f"   - {milestone['name']}: {milestone_duration}\n"
            
        summary += """
4. Required Agents:
"""
        for agent in self.project_scope.required_agents:
            summary += f"   - {agent}\n"
            
        summary += """
Would you like to proceed with this plan? I can also adjust any aspects based on your feedback."""
        
        return summary
        
    def _format_duration(self, seconds: float) -> str:
        """Format duration in a human-readable way."""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutes"
        elif seconds < 86400:
            return f"{seconds/3600:.1f} hours"
        else:
            return f"{seconds/86400:.1f} days"
            
    async def process_document(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Process uploaded documents for additional requirements."""
        try:
            content = await self._read_document(file_path, file_type)
            analysis = await self.llm.analyze_text(
                content,
                "Extract key requirements and specifications from this document."
            )
            
            # Update project scope with new information
            await self._update_scope_with_document(analysis)
            
            return {
                "status": "success",
                "message": "Document processed successfully",
                "new_requirements": len(analysis.get("requirements", [])),
                "updated_scope": bool(analysis.get("scope_updates"))
            }
            
        except Exception as e:
            logger.error(f"Failed to process document: {e}")
            raise
            
    async def _read_document(self, file_path: str, file_type: str) -> str:
        """Read different types of documents."""
        if file_type == "pdf":
            return await self._read_pdf(file_path)
        elif file_type == "docx":
            return await self._read_docx(file_path)
        elif file_type == "xlsx":
            return await self._read_excel(file_path)
        elif file_type == "txt":
            return await self._read_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
    async def _read_pdf(self, file_path: str) -> str:
        """Read PDF files."""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
        
    async def _read_docx(self, file_path: str) -> str:
        """Read DOCX files."""
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
    async def _read_excel(self, file_path: str) -> str:
        """Read Excel files."""
        df = pd.read_excel(file_path)
        return df.to_string()
        
    async def _read_text(self, file_path: str) -> str:
        """Read text files."""
        with open(file_path, 'r') as file:
            return file.read()
            
    async def process_website(self, url: str) -> Dict[str, Any]:
        """Process website content for additional requirements."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
                    
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            
            analysis = await self.llm.analyze_text(
                text_content,
                "Extract key requirements and specifications from this website content."
            )
            
            # Update project scope with new information
            await self._update_scope_with_document(analysis)
            
            return {
                "status": "success",
                "message": "Website processed successfully",
                "new_requirements": len(analysis.get("requirements", [])),
                "updated_scope": bool(analysis.get("scope_updates"))
            }
            
        except Exception as e:
            logger.error(f"Failed to process website: {e}")
            raise
            
    async def process_voice(self, audio_data: bytes) -> Dict[str, Any]:
        """Process voice input for additional requirements."""
        try:
            recognizer = sr.Recognizer()
            audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
            text = recognizer.recognize_google(audio)
            
            analysis = await self.llm.analyze_text(
                text,
                "Extract key requirements and specifications from this voice input."
            )
            
            # Update project scope with new information
            await self._update_scope_with_document(analysis)
            
            return {
                "status": "success",
                "message": "Voice input processed successfully",
                "new_requirements": len(analysis.get("requirements", [])),
                "updated_scope": bool(analysis.get("scope_updates"))
            }
            
        except Exception as e:
            logger.error(f"Failed to process voice input: {e}")
            raise
            
    async def _update_scope_with_document(self, analysis: Dict[str, Any]):
        """Update project scope with information from documents."""
        if "requirements" in analysis:
            new_requirements = [ProjectRequirement(**req) for req in analysis["requirements"]]
            self.requirements.extend(new_requirements)
            
        if "scope_updates" in analysis:
            updates = analysis["scope_updates"]
            for key, value in updates.items():
                if hasattr(self.project_scope, key):
                    setattr(self.project_scope, key, value)
                    
        # Recalculate timeline with new information
        timeline = await self._calculate_timeline()
        self.project_scope.milestones = timeline["milestones"]
        self.project_scope.total_estimated_duration = timeline["total_duration"] 