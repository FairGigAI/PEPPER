"""Script to reorganize agents into specialized directories and update configurations."""

import os
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import re

# Define agent specializations
AGENT_SPECIALIZATIONS = {
    'pm_agent.py': 'project_management',
    'slack_bot_agent.py': 'communication',
    'documentation_agent.py': 'documentation',
    'timeline_estimator_agent.py': 'timeline_estimation',
    'security_agent.py': 'security',
    'infra_agent.py': 'infrastructure',
    'ai_architect_agent.py': 'ai_architecture',
    'qa_agent.py': 'qa',
    'client_intake_agent.py': 'client_intake'
}

def create_specialized_directories(base_path: str) -> None:
    """Create specialized directories for agents."""
    specialized_dir = os.path.join(base_path, 'agents', 'specialized')
    for specialization in set(AGENT_SPECIALIZATIONS.values()):
        dir_path = os.path.join(specialized_dir, specialization)
        os.makedirs(dir_path, exist_ok=True)
        # Create __init__.py
        init_file = os.path.join(dir_path, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('"""Specialized agent module."""\n\n')

def move_agent_files(base_path: str) -> List[Tuple[str, str]]:
    """Move agent files to their specialized directories."""
    moved_files = []
    agents_dir = os.path.join(base_path, 'agents')
    
    for agent_file, specialization in AGENT_SPECIALIZATIONS.items():
        source_path = os.path.join(agents_dir, agent_file)
        if not os.path.exists(source_path):
            print(f"Warning: {agent_file} not found")
            continue
            
        target_dir = os.path.join(agents_dir, 'specialized', specialization)
        target_path = os.path.join(target_dir, agent_file)
        
        try:
            shutil.move(source_path, target_path)
            moved_files.append((source_path, target_path))
            print(f"Moved {agent_file} to {specialization}/")
        except Exception as e:
            print(f"Error moving {agent_file}: {e}")
    
    return moved_files

def update_imports(file_path: str) -> None:
    """Update import statements in moved files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encodings
        for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            print(f"Warning: Could not read {file_path} with any supported encoding")
            return
    
    # Update relative imports
    new_content = re.sub(
        r'from \.\.\.agents\.',
        'from ...agents.specialized.',
        content
    )
    
    # Update absolute imports
    new_content = re.sub(
        r'from agents\.',
        'from agents.specialized.',
        new_content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def update_config_files(base_path: str) -> None:
    """Update configuration files to match new structure."""
    config_dir = os.path.join(base_path, 'core', 'config', 'agents')
    
    for agent_file, specialization in AGENT_SPECIALIZATIONS.items():
        config_file = agent_file.replace('.py', '.yaml')
        config_path = os.path.join(config_dir, config_file)
        
        if not os.path.exists(config_path):
            print(f"Warning: Config file {config_file} not found")
            continue
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Update agent path in config
            if 'agent_path' in config:
                config['agent_path'] = f'agents.specialized.{specialization}.{agent_file[:-3]}'
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"Updated config file {config_file}")
        except Exception as e:
            print(f"Error updating {config_file}: {e}")

def update_test_files(base_path: str) -> None:
    """Update test files to match new structure."""
    tests_dir = os.path.join(base_path, 'tests', 'agents')
    
    for agent_file, specialization in AGENT_SPECIALIZATIONS.items():
        test_file = f"test_{agent_file}"
        test_path = os.path.join(tests_dir, test_file)
        
        if not os.path.exists(test_path):
            print(f"Warning: Test file {test_file} not found")
            continue
            
        try:
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update import paths
            new_content = re.sub(
                r'from agents\.',
                f'from agents.specialized.{specialization}.',
                content
            )
            
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"Updated test file {test_file}")
        except Exception as e:
            print(f"Error updating {test_file}: {e}")

def main():
    """Main function to reorganize agents and update configurations."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("Creating specialized directories...")
    create_specialized_directories(base_path)
    
    print("\nMoving agent files...")
    moved_files = move_agent_files(base_path)
    
    print("\nUpdating imports in moved files...")
    for _, target_path in moved_files:
        update_imports(target_path)
    
    print("\nUpdating configuration files...")
    update_config_files(base_path)
    
    print("\nUpdating test files...")
    update_test_files(base_path)
    
    print("\nReorganization complete!")

if __name__ == "__main__":
    main() 