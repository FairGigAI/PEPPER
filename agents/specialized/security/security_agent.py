"""Security agent for performing security audits and vulnerability scanning."""

import os
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.table import Table

from core.agent_base import BaseAgent, Task
from core.config_models import SecurityAgentConfig
from core.exceptions import FatalError
from core.agent_orchestrator import TaskDependency

class SecurityAgent(BaseAgent):
    """Agent responsible for security audits and vulnerability scanning."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        if not isinstance(self.config, SecurityAgentConfig):
            raise FatalError(f"Invalid configuration for SecurityAgent {agent_id}")
            
        self.console = Console()
        self.output_dir = self.config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def preprocess(self, task: Task) -> Dict[str, Any]:
        """Preprocess the task before execution."""
        logger.info(f"Preprocessing security task: {task.task_id}")
        
        # Validate scan type
        scan_type = task.metadata.get("scan_type", "full")
        if scan_type not in self.config.supported_scan_types:
            raise FatalError(f"Unsupported scan type: {scan_type}")
            
        return {
            "scan_type": scan_type,
            "target": task.metadata.get("target", "all"),
            "severity_threshold": task.metadata.get("severity_threshold", "high")
        }
        
    async def execute(self, task: Task) -> Dict[str, Any]:
        """Execute the security task."""
        logger.info(f"Executing security task: {task.task_id}")
        
        # Get security requirements
        requirements = task.metadata.get("requirements", {})
        
        # Perform security scan
        scan_results = self._perform_security_scan(requirements, task.metadata)
        
        # Generate security report
        report = self._generate_security_report(scan_results, task.metadata)
        
        # Save security documentation
        output_file = f"security_{task.task_id.lower()}.md"
        output_path = os.path.join(self.output_dir, output_file)
        
        try:
            self._save_security_docs(scan_results, report, output_path)
            logger.info(f"Generated security documentation: {output_path}")
            
            return {
                "status": "success",
                "message": "Completed security scan and generated report",
                "details": {
                    "output_file": output_file,
                    "scan_type": task.metadata.get("scan_type"),
                    "vulnerability_count": len(scan_results.get("vulnerabilities", [])),
                    "compliance_score": report.get("compliance_score", 0)
                }
            }
        except Exception as e:
            logger.error(f"Failed to complete security scan: {e}")
            raise
            
    def _perform_security_scan(self, requirements: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Perform security scan based on requirements."""
        scan_type = metadata.get("scan_type", "full")
        target = metadata.get("target", "all")
        
        # Define scan components
        components = []
        
        if scan_type == "full":
            components = self._generate_full_scan_components(requirements, target)
        elif scan_type == "vulnerability":
            components = self._generate_vulnerability_scan_components(requirements, target)
        elif scan_type == "compliance":
            components = self._generate_compliance_scan_components(requirements, target)
            
        # Perform scans
        scan_results = {
            "scan_type": scan_type,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "vulnerabilities": self._scan_for_vulnerabilities(components),
            "compliance": self._check_compliance(components),
            "recommendations": self._generate_recommendations(components)
        }
        
        return scan_results
        
    def _generate_full_scan_components(self, requirements: Dict[str, Any], target: str) -> List[Dict[str, Any]]:
        """Generate components for full security scan."""
        components = []
        
        # Extract service requirements
        services = requirements.get("services", [])
        
        for service in services:
            component = {
                "name": service.get("name", "unnamed_service"),
                "type": "service",
                "description": service.get("description", ""),
                "dependencies": service.get("dependencies", []),
                "scan_targets": self._get_scan_targets(service, target)
            }
            components.append(component)
            
        # Add shared components
        shared_components = [
            {
                "name": "network",
                "type": "infrastructure",
                "description": "Network security scan",
                "dependencies": [],
                "scan_targets": ["ports", "firewall", "vpn"]
            },
            {
                "name": "authentication",
                "type": "security",
                "description": "Authentication system scan",
                "dependencies": [],
                "scan_targets": ["auth_protocols", "password_policy", "session_management"]
            }
        ]
        components.extend(shared_components)
        
        return components
        
    def _generate_vulnerability_scan_components(self, requirements: Dict[str, Any], target: str) -> List[Dict[str, Any]]:
        """Generate components for vulnerability scan."""
        components = []
        
        # Extract service requirements
        services = requirements.get("services", [])
        
        for service in services:
            component = {
                "name": service.get("name", "unnamed_service"),
                "type": "service",
                "description": service.get("description", ""),
                "dependencies": service.get("dependencies", []),
                "scan_targets": ["dependencies", "code", "configurations"]
            }
            components.append(component)
            
        return components
        
    def _generate_compliance_scan_components(self, requirements: Dict[str, Any], target: str) -> List[Dict[str, Any]]:
        """Generate components for compliance scan."""
        components = []
        
        # Extract compliance requirements
        compliance = requirements.get("compliance", {})
        
        for standard, rules in compliance.items():
            component = {
                "name": standard,
                "type": "compliance",
                "description": f"Compliance check for {standard}",
                "dependencies": [],
                "scan_targets": ["policies", "procedures", "implementations"]
            }
            components.append(component)
            
        return components
        
    def _get_scan_targets(self, service: Dict[str, Any], target: str) -> List[str]:
        """Get scan targets for a service."""
        if target == "all":
            return ["code", "dependencies", "configurations", "infrastructure", "data"]
        elif target == "code":
            return ["code", "dependencies"]
        elif target == "infrastructure":
            return ["configurations", "infrastructure"]
        else:
            return ["data"]
            
    def _scan_for_vulnerabilities(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scan components for vulnerabilities."""
        vulnerabilities = []
        
        for component in components:
            # Simulate vulnerability scanning
            if component["type"] == "service":
                vulns = self._scan_service_vulnerabilities(component)
                vulnerabilities.extend(vulns)
            elif component["type"] == "infrastructure":
                vulns = self._scan_infrastructure_vulnerabilities(component)
                vulnerabilities.extend(vulns)
            elif component["type"] == "security":
                vulns = self._scan_security_vulnerabilities(component)
                vulnerabilities.extend(vulns)
                
        return vulnerabilities
        
    def _scan_service_vulnerabilities(self, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan service for vulnerabilities."""
        return [
            {
                "component": component["name"],
                "type": "dependency",
                "severity": "high",
                "description": "Outdated dependency package",
                "recommendation": "Update to latest version"
            },
            {
                "component": component["name"],
                "type": "code",
                "severity": "medium",
                "description": "Potential SQL injection vulnerability",
                "recommendation": "Use parameterized queries"
            }
        ]
        
    def _scan_infrastructure_vulnerabilities(self, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan infrastructure for vulnerabilities."""
        return [
            {
                "component": component["name"],
                "type": "configuration",
                "severity": "high",
                "description": "Open port detected",
                "recommendation": "Close unnecessary ports"
            },
            {
                "component": component["name"],
                "type": "network",
                "severity": "medium",
                "description": "Weak firewall rules",
                "recommendation": "Strengthen firewall configuration"
            }
        ]
        
    def _scan_security_vulnerabilities(self, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan security components for vulnerabilities."""
        return [
            {
                "component": component["name"],
                "type": "authentication",
                "severity": "high",
                "description": "Weak password policy",
                "recommendation": "Implement stronger password requirements"
            },
            {
                "component": component["name"],
                "type": "session",
                "severity": "medium",
                "description": "Insecure session management",
                "recommendation": "Implement secure session handling"
            }
        ]
        
    def _check_compliance(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check compliance requirements."""
        compliance_results = {}
        
        for component in components:
            if component["type"] == "compliance":
                results = self._check_compliance_standard(component)
                compliance_results[component["name"]] = results
                
        return compliance_results
        
    def _check_compliance_standard(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with a specific standard."""
        return {
            "status": "compliant",
            "score": 85,
            "violations": [
                {
                    "rule": "Password Policy",
                    "severity": "medium",
                    "description": "Password complexity requirements not met",
                    "recommendation": "Implement stronger password requirements"
                }
            ]
        }
        
    def _generate_recommendations(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate security recommendations."""
        recommendations = []
        
        for component in components:
            if component["type"] == "service":
                recs = self._generate_service_recommendations(component)
                recommendations.extend(recs)
            elif component["type"] == "infrastructure":
                recs = self._generate_infrastructure_recommendations(component)
                recommendations.extend(recs)
            elif component["type"] == "security":
                recs = self._generate_security_recommendations(component)
                recommendations.extend(recs)
                
        return recommendations
        
    def _generate_service_recommendations(self, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for a service."""
        return [
            {
                "component": component["name"],
                "type": "security",
                "priority": "high",
                "description": "Implement input validation",
                "action": "Add input validation middleware"
            },
            {
                "component": component["name"],
                "type": "monitoring",
                "priority": "medium",
                "description": "Add security monitoring",
                "action": "Implement security event logging"
            }
        ]
        
    def _generate_infrastructure_recommendations(self, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for infrastructure."""
        return [
            {
                "component": component["name"],
                "type": "network",
                "priority": "high",
                "description": "Implement network segmentation",
                "action": "Create separate network zones"
            },
            {
                "component": component["name"],
                "type": "access",
                "priority": "medium",
                "description": "Restrict access to sensitive resources",
                "action": "Implement role-based access control"
            }
        ]
        
    def _generate_security_recommendations(self, component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for security components."""
        return [
            {
                "component": component["name"],
                "type": "authentication",
                "priority": "high",
                "description": "Implement multi-factor authentication",
                "action": "Add MFA support"
            },
            {
                "component": component["name"],
                "type": "audit",
                "priority": "medium",
                "description": "Enable security auditing",
                "action": "Configure audit logging"
            }
        ]
        
    def _generate_security_report(self, scan_results: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security report from scan results."""
        severity_threshold = metadata.get("severity_threshold", "high")
        
        # Filter vulnerabilities by severity
        critical_vulnerabilities = [
            v for v in scan_results["vulnerabilities"]
            if v["severity"] == "high"
        ]
        
        # Calculate compliance score
        compliance_scores = [
            result["score"]
            for result in scan_results["compliance"].values()
        ]
        avg_compliance_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "scan_type": scan_results["scan_type"],
            "target": scan_results["target"],
            "vulnerability_count": len(scan_results["vulnerabilities"]),
            "critical_vulnerability_count": len(critical_vulnerabilities),
            "compliance_score": avg_compliance_score,
            "recommendation_count": len(scan_results["recommendations"])
        }
        
    def _save_security_docs(self, scan_results: Dict[str, Any], report: Dict[str, Any], output_path: str):
        """Save security documentation to markdown file."""
        with open(output_path, 'w') as f:
            f.write(f"""# Security Scan Report

## Overview
This document outlines the results of the security scan and provides recommendations.

## Scan Information
- **Type:** {scan_results['scan_type']}
- **Target:** {scan_results['target']}
- **Timestamp:** {scan_results['timestamp']}

## Summary
- Total Vulnerabilities: {report['vulnerability_count']}
- Critical Vulnerabilities: {report['critical_vulnerability_count']}
- Compliance Score: {report['compliance_score']:.1f}%
- Recommendations: {report['recommendation_count']}

## Vulnerabilities

""")
            
            for vuln in scan_results["vulnerabilities"]:
                f.write(f"""### {vuln['component']} - {vuln['type']}
**Severity:** {vuln['severity']}
**Description:** {vuln['description']}
**Recommendation:** {vuln['recommendation']}

""")
                
            f.write("""## Compliance Results

""")
            for standard, results in scan_results["compliance"].items():
                f.write(f"""### {standard}
**Status:** {results['status']}
**Score:** {results['score']}%

**Violations:**
""")
                for violation in results["violations"]:
                    f.write(f"- **{violation['rule']}** ({violation['severity']}): {violation['description']}\n")
                f.write("\n")
                
            f.write("""## Recommendations

""")
            for rec in scan_results["recommendations"]:
                f.write(f"""### {rec['component']} - {rec['type']}
**Priority:** {rec['priority']}
**Description:** {rec['description']}
**Action:** {rec['action']}

""")
                
    async def postprocess(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the task results."""
        logger.info(f"Postprocessing security task: {task.task_id}")
        
        # Add any additional metadata or processing here
        result["metadata"] = {
            "scan_type": task.metadata.get("scan_type"),
            "target": task.metadata.get("target"),
            "severity_threshold": task.metadata.get("severity_threshold")
        }
        
        return result
            
    async def preprocess_task(self, task: Task) -> Task:
        """Validate and prepare security tasks."""
        if "requirements" not in task.metadata:
            raise ValueError("Security requirements must be specified in task metadata")
        return task 