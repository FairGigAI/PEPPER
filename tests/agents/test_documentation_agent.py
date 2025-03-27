"""Tests for the DocumentationAgent."""

import pytest
from pathlib import Path
from typing import Dict, Any
from agents.specialized.documentation.documentation_agent import DocumentationAgent
from core.exceptions import FatalError

@pytest.mark.asyncio
async def test_agent_initialization(doc_agent_config: Dict[str, Any], temp_dir: Path):
    """Test DocumentationAgent initialization."""
    agent = DocumentationAgent("test_agent", doc_agent_config)
    assert agent.agent_id == "test_agent"
    assert agent.output_dir == "docs"
    assert agent.templates_dir == "templates"

@pytest.mark.asyncio
async def test_preprocess_validation(doc_agent_config: Dict[str, Any], sample_task: Task):
    """Test task preprocessing validation."""
    agent = DocumentationAgent("test_agent", doc_agent_config)
    
    # Test valid doc_type
    result = await agent.preprocess(sample_task)
    assert result["doc_type"] == "markdown"
    
    # Test invalid doc_type
    invalid_task = sample_task.copy()
    invalid_task.metadata["doc_type"] = "invalid"
    with pytest.raises(FatalError):
        await agent.preprocess(invalid_task)

@pytest.mark.asyncio
async def test_documentation_generation(doc_agent_config: Dict[str, Any], sample_task: Task, temp_dir: Path):
    """Test documentation generation."""
    agent = DocumentationAgent("test_agent", doc_agent_config)
    
    # Create test template
    template_dir = Path(temp_dir) / "templates"
    template_dir.mkdir()
    template_file = template_dir / "api_doc.md"
    template_file.write_text("""# {{title}}

## Overview
{{overview}}

## Usage
{{usage}}

## Configuration
{{configuration}}
""")
    
    # Generate documentation
    result = await agent.execute(sample_task)
    assert result["status"] == "success"
    assert "output_file" in result
    assert Path(result["output_file"]).exists()

@pytest.mark.asyncio
async def test_documentation_update(doc_agent_config: Dict[str, Any], temp_dir: Path):
    """Test documentation update functionality."""
    agent = DocumentationAgent("test_agent", doc_agent_config)
    
    # Create initial document
    doc_path = Path(temp_dir) / "test_doc.md"
    doc_path.write_text("# Initial Document\n\n## Overview\nInitial content")
    
    # Create update task
    update_task = Task(
        task_id="test-002",
        task_type="documentation.update",
        description="Update documentation",
        metadata={
            "doc_type": "markdown",
            "file_path": str(doc_path),
            "updates": {
                "overview": "Updated content"
            }
        }
    )
    
    # Update documentation
    result = await agent.execute(update_task)
    assert result["status"] == "success"
    
    # Verify update
    updated_content = doc_path.read_text()
    assert "Updated content" in updated_content

@pytest.mark.asyncio
async def test_documentation_review(doc_agent_config: Dict[str, Any], sample_markdown_content: str, temp_dir: Path):
    """Test documentation review functionality."""
    agent = DocumentationAgent("test_agent", doc_agent_config)
    
    # Create test document
    doc_path = Path(temp_dir) / "review_test.md"
    doc_path.write_text(sample_markdown_content)
    
    # Create review task
    review_task = Task(
        task_id="test-003",
        task_type="documentation.review",
        description="Review documentation",
        metadata={
            "doc_type": "markdown",
            "file_path": str(doc_path),
            "review_criteria": ["completeness", "clarity", "formatting"]
        }
    )
    
    # Review documentation
    result = await agent.execute(review_task)
    assert result["status"] == "success"
    assert "review_results" in result
    assert "suggestions" in result["review_results"]

@pytest.mark.asyncio
async def test_template_validation(doc_agent_config: Dict[str, Any], temp_dir: Path):
    """Test template validation."""
    agent = DocumentationAgent("test_agent", doc_agent_config)
    
    # Create invalid template
    template_dir = Path(temp_dir) / "templates"
    template_dir.mkdir()
    invalid_template = template_dir / "invalid.md"
    invalid_template.write_text("{{invalid_variable}}")
    
    # Test with invalid template
    task = Task(
        task_id="test-004",
        task_type="documentation.generate",
        description="Test invalid template",
        metadata={
            "doc_type": "markdown",
            "template": "invalid"
        }
    )
    
    with pytest.raises(FatalError):
        await agent.execute(task)

@pytest.mark.asyncio
async def test_cross_reference_validation(doc_agent_config: Dict[str, Any], temp_dir: Path):
    """Test cross-reference validation."""
    agent = DocumentationAgent("test_agent", doc_agent_config)
    
    # Create test documents with cross-references
    docs_dir = Path(temp_dir) / "docs"
    docs_dir.mkdir()
    
    doc1 = docs_dir / "doc1.md"
    doc1.write_text("# Doc 1\n\nSee [Doc 2](doc2.md) for more info.")
    
    doc2 = docs_dir / "doc2.md"
    doc2.write_text("# Doc 2\n\nSee [Doc 1](doc1.md) for more info.")
    
    # Create validation task
    validation_task = Task(
        task_id="test-005",
        task_type="documentation.validate",
        description="Validate cross-references",
        metadata={
            "doc_type": "markdown",
            "files": [str(doc1), str(doc2)],
            "check_cross_references": True
        }
    )
    
    # Validate cross-references
    result = await agent.execute(validation_task)
    assert result["status"] == "success"
    assert "validation_results" in result
    assert "cross_references" in result["validation_results"] 