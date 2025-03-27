"""Infrastructure agent for managing system infrastructure and deployment."""

import os
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.table import Table

from core.agent_base import BaseAgent, Task
from core.config_models import InfraAgentConfig
from core.exceptions import FatalError
from core.agent_orchestrator import TaskDependency

class InfraAgent(BaseAgent):
    """Agent responsible for managing system infrastructure and deployment."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        if not isinstance(self.config, InfraAgentConfig):
            raise FatalError(f"Invalid configuration for InfraAgent {agent_id}")
            
        self.console = Console()
        self.output_dir = self.config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing infrastructure task: {task.task_id}")
        
        # Validate infrastructure type
        infra_type = task.metadata.get("infrastructure_type", "cloud")
        if infra_type not in self.config.supported_infrastructure:
            raise FatalError(f"Unsupported infrastructure type: {infra_type}")
            
        return {
            "infrastructure_type": infra_type,
            "provider": task.metadata.get("provider", "aws"),
            "region": task.metadata.get("region", "us-east-1")
        }
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the infrastructure task."""
        logger.info(f"Executing infrastructure task: {task.task_id}")
        
        # Get infrastructure requirements
        requirements = task.metadata.get("requirements", {})
        
        # Generate infrastructure plan
        infrastructure_plan = self._generate_infrastructure_plan(requirements, task.metadata)
        
        # Generate deployment scripts
        deployment_scripts = self._generate_deployment_scripts(infrastructure_plan, task.metadata)
        
        # Save infrastructure documentation
        output_file = f"infrastructure_{task.task_id.lower()}.md"
        output_path = os.path.join(self.output_dir, output_file)
        
        try:
            self._save_infrastructure_docs(infrastructure_plan, deployment_scripts, output_path)
            logger.info(f"Generated infrastructure documentation: {output_path}")
            
            return {
                "status": "success",
                "message": "Generated infrastructure plan and deployment scripts",
                "details": {
                    "output_file": output_file,
                    "infrastructure_type": task.metadata.get("infrastructure_type"),
                    "resource_count": len(infrastructure_plan.get("resources", [])),
                    "script_count": len(deployment_scripts)
                }
            }
        except Exception as e:
            logger.error(f"Failed to generate infrastructure plan: {e}")
            raise
            
    def _generate_infrastructure_plan(self, requirements: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate infrastructure plan based on requirements."""
        infra_type = metadata.get("infrastructure_type", "cloud")
        provider = metadata.get("provider", "aws")
        
        # Define infrastructure resources
        resources = []
        
        if infra_type == "cloud":
            resources = self._generate_cloud_resources(requirements, provider)
        elif infra_type == "on_premise":
            resources = self._generate_on_premise_resources(requirements)
        elif infra_type == "hybrid":
            resources = self._generate_hybrid_resources(requirements, provider)
            
        # Generate networking configuration
        networking = self._generate_networking_config(infra_type, provider)
        
        return {
            "infrastructure_type": infra_type,
            "provider": provider,
            "resources": resources,
            "networking": networking,
            "requirements": requirements
        }
        
    def _generate_cloud_resources(self, requirements: Dict[str, Any], provider: str) -> List[Dict[str, Any]]:
        """Generate cloud infrastructure resources."""
        resources = []
        
        # Extract service requirements
        services = requirements.get("services", [])
        
        for service in services:
            resource = {
                "name": service.get("name", "unnamed_service"),
                "type": "service",
                "provider": provider,
                "description": service.get("description", ""),
                "dependencies": service.get("dependencies", []),
                "scale": service.get("scale", "medium"),
                "resources": self._calculate_cloud_resources(service, provider)
            }
            resources.append(resource)
            
        # Add shared resources
        shared_resources = [
            {
                "name": "vpc",
                "type": "network",
                "provider": provider,
                "description": "Virtual Private Cloud",
                "dependencies": [],
                "cidr": "10.0.0.0/16"
            },
            {
                "name": "security_group",
                "type": "security",
                "provider": provider,
                "description": "Security group for services",
                "dependencies": ["vpc"],
                "rules": self._generate_security_rules()
            }
        ]
        resources.extend(shared_resources)
        
        return resources
        
    def _generate_on_premise_resources(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate on-premise infrastructure resources."""
        resources = []
        
        # Extract service requirements
        services = requirements.get("services", [])
        
        for service in services:
            resource = {
                "name": service.get("name", "unnamed_service"),
                "type": "service",
                "provider": "on_premise",
                "description": service.get("description", ""),
                "dependencies": service.get("dependencies", []),
                "scale": service.get("scale", "medium"),
                "resources": self._calculate_on_premise_resources(service)
            }
            resources.append(resource)
            
        # Add shared resources
        shared_resources = [
            {
                "name": "network",
                "type": "network",
                "provider": "on_premise",
                "description": "Internal network",
                "dependencies": [],
                "subnet": "192.168.1.0/24"
            },
            {
                "name": "firewall",
                "type": "security",
                "provider": "on_premise",
                "description": "Network firewall",
                "dependencies": ["network"],
                "rules": self._generate_security_rules()
            }
        ]
        resources.extend(shared_resources)
        
        return resources
        
    def _generate_hybrid_resources(self, requirements: Dict[str, Any], provider: str) -> List[Dict[str, Any]]:
        """Generate hybrid infrastructure resources."""
        resources = []
        
        # Generate cloud resources
        cloud_resources = self._generate_cloud_resources(requirements, provider)
        resources.extend(cloud_resources)
        
        # Generate on-premise resources
        on_premise_resources = self._generate_on_premise_resources(requirements)
        resources.extend(on_premise_resources)
        
        # Add hybrid-specific resources
        hybrid_resources = [
            {
                "name": "vpn",
                "type": "network",
                "provider": "hybrid",
                "description": "VPN connection between cloud and on-premise",
                "dependencies": ["vpc", "network"],
                "protocol": "ipsec"
            }
        ]
        resources.extend(hybrid_resources)
        
        return resources
        
    def _generate_networking_config(self, infra_type: str, provider: str) -> Dict[str, Any]:
        """Generate networking configuration."""
        if infra_type == "cloud":
            return {
                "type": "cloud",
                "provider": provider,
                "vpc": {
                    "cidr": "10.0.0.0/16",
                    "subnets": ["public", "private"],
                    "nat_gateway": True
                },
                "dns": {
                    "type": "route53",
                    "zones": ["internal", "external"]
                }
            }
        elif infra_type == "on_premise":
            return {
                "type": "on_premise",
                "network": {
                    "subnet": "192.168.1.0/24",
                    "gateway": "192.168.1.1",
                    "dns": ["8.8.8.8", "8.8.4.4"]
                }
            }
        else:
            return {
                "type": "hybrid",
                "cloud": {
                    "provider": provider,
                    "vpc": {
                        "cidr": "10.0.0.0/16",
                        "subnets": ["public", "private"],
                        "nat_gateway": True
                    }
                },
                "on_premise": {
                    "network": {
                        "subnet": "192.168.1.0/24",
                        "gateway": "192.168.1.1",
                        "dns": ["8.8.8.8", "8.8.4.4"]
                    }
                },
                "vpn": {
                    "protocol": "ipsec",
                    "tunnels": 2
                }
            }
            
    def _generate_deployment_scripts(self, infrastructure_plan: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate deployment scripts for infrastructure."""
        scripts = []
        
        # Generate provider-specific scripts
        provider = metadata.get("provider", "aws")
        if provider == "aws":
            scripts.extend(self._generate_aws_scripts(infrastructure_plan))
        elif provider == "azure":
            scripts.extend(self._generate_azure_scripts(infrastructure_plan))
        elif provider == "gcp":
            scripts.extend(self._generate_gcp_scripts(infrastructure_plan))
            
        # Generate common scripts
        common_scripts = [
            {
                "name": "deploy.sh",
                "type": "shell",
                "description": "Main deployment script",
                "content": self._generate_deploy_script(infrastructure_plan)
            },
            {
                "name": "destroy.sh",
                "type": "shell",
                "description": "Infrastructure cleanup script",
                "content": self._generate_destroy_script(infrastructure_plan)
            }
        ]
        scripts.extend(common_scripts)
        
        return scripts
        
    def _generate_aws_scripts(self, infrastructure_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AWS-specific deployment scripts."""
        return [
            {
                "name": "aws_infrastructure.tf",
                "type": "terraform",
                "description": "AWS infrastructure Terraform configuration",
                "content": self._generate_aws_terraform(infrastructure_plan)
            },
            {
                "name": "aws_variables.tf",
                "type": "terraform",
                "description": "AWS Terraform variables",
                "content": self._generate_aws_variables(infrastructure_plan)
            }
        ]
        
    def _generate_azure_scripts(self, infrastructure_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Azure-specific deployment scripts."""
        return [
            {
                "name": "azure_infrastructure.tf",
                "type": "terraform",
                "description": "Azure infrastructure Terraform configuration",
                "content": self._generate_azure_terraform(infrastructure_plan)
            },
            {
                "name": "azure_variables.tf",
                "type": "terraform",
                "description": "Azure Terraform variables",
                "content": self._generate_azure_variables(infrastructure_plan)
            }
        ]
        
    def _generate_gcp_scripts(self, infrastructure_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate GCP-specific deployment scripts."""
        return [
            {
                "name": "gcp_infrastructure.tf",
                "type": "terraform",
                "description": "GCP infrastructure Terraform configuration",
                "content": self._generate_gcp_terraform(infrastructure_plan)
            },
            {
                "name": "gcp_variables.tf",
                "type": "terraform",
                "description": "GCP Terraform variables",
                "content": self._generate_gcp_variables(infrastructure_plan)
            }
        ]
        
    def _generate_deploy_script(self, infrastructure_plan: Dict[str, Any]) -> str:
        """Generate main deployment script."""
        return f"""#!/bin/bash

# Infrastructure deployment script
# Generated for {infrastructure_plan['infrastructure_type']} infrastructure

# Initialize Terraform
terraform init

# Apply infrastructure changes
terraform apply -auto-approve

# Output deployment information
terraform output
"""
        
    def _generate_destroy_script(self, infrastructure_plan: Dict[str, Any]) -> str:
        """Generate infrastructure cleanup script."""
        return f"""#!/bin/bash

# Infrastructure cleanup script
# Generated for {infrastructure_plan['infrastructure_type']} infrastructure

# Destroy infrastructure
terraform destroy -auto-approve

# Clean up local files
rm -rf .terraform
rm -f terraform.tfstate*
"""
        
    def _calculate_cloud_resources(self, service: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Calculate cloud resource requirements."""
        scale = service.get("scale", "medium")
        
        if provider == "aws":
            if scale == "small":
                return {"instance_type": "t2.small", "count": 1}
            elif scale == "medium":
                return {"instance_type": "t2.medium", "count": 2}
            else:
                return {"instance_type": "t2.large", "count": 3}
        elif provider == "azure":
            if scale == "small":
                return {"vm_size": "Standard_B1s", "count": 1}
            elif scale == "medium":
                return {"vm_size": "Standard_B2s", "count": 2}
            else:
                return {"vm_size": "Standard_B4ms", "count": 3}
        else:  # GCP
            if scale == "small":
                return {"machine_type": "e2-small", "count": 1}
            elif scale == "medium":
                return {"machine_type": "e2-medium", "count": 2}
            else:
                return {"machine_type": "e2-standard-2", "count": 3}
                
    def _calculate_on_premise_resources(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate on-premise resource requirements."""
        scale = service.get("scale", "medium")
        
        if scale == "small":
            return {"cpu": 2, "memory": "4Gi", "storage": "50Gi"}
        elif scale == "medium":
            return {"cpu": 4, "memory": "8Gi", "storage": "100Gi"}
        else:
            return {"cpu": 8, "memory": "16Gi", "storage": "200Gi"}
            
    def _generate_security_rules(self) -> List[Dict[str, Any]]:
        """Generate security rules for infrastructure."""
        return [
            {
                "type": "ingress",
                "protocol": "tcp",
                "port": 80,
                "source": "0.0.0.0/0",
                "description": "HTTP access"
            },
            {
                "type": "ingress",
                "protocol": "tcp",
                "port": 443,
                "source": "0.0.0.0/0",
                "description": "HTTPS access"
            },
            {
                "type": "ingress",
                "protocol": "tcp",
                "port": 22,
                "source": "0.0.0.0/0",
                "description": "SSH access"
            }
        ]
        
    def _save_infrastructure_docs(self, infrastructure_plan: Dict[str, Any], deployment_scripts: List[Dict[str, Any]], output_path: str):
        """Save infrastructure documentation to markdown file."""
        with open(output_path, 'w') as f:
            f.write(f"""# Infrastructure Plan

## Overview
This document outlines the infrastructure plan and deployment scripts for the project.

## Infrastructure Type
{infrastructure_plan['infrastructure_type']}

## Provider
{infrastructure_plan['provider']}

## Resources

""")
            
            for resource in infrastructure_plan["resources"]:
                f.write(f"""### {resource['name']}
**Type:** {resource['type']}
**Provider:** {resource['provider']}
**Description:** {resource['description']}

**Dependencies:**
{', '.join(resource['dependencies']) if resource['dependencies'] else 'None'}

**Scale:** {resource['scale']}
**Resources:** {resource.get('resources', 'N/A')}

""")
                
            f.write("""## Networking Configuration

""")
            for key, value in infrastructure_plan["networking"].items():
                f.write(f"- **{key}:** {value}\n")
                
            f.write("""\n## Deployment Scripts

""")
            for script in deployment_scripts:
                f.write(f"""### {script['name']}
**Type:** {script['type']}
**Description:** {script['description']}

```{script['type']}
{script['content']}
```

""")
                
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing infrastructure task: {task.task_id}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "infrastructure_type": task.metadata.get("infrastructure_type"),
            "provider": task.metadata.get("provider"),
            "region": task.metadata.get("region")
        }
        
        return result
            
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare infrastructure tasks."""
        if "requirements" not in task.metadata:
            raise ValueError("Infrastructure requirements must be specified in task metadata")
        return task 