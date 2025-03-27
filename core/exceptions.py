"""Custom exceptions for P.E.P.P.E.R."""

class AgentError(Exception):
    """Base exception for all agent-related errors."""
    pass

class TransientError(AgentError):
    """Exception for transient errors that may resolve themselves."""
    pass

class FatalError(AgentError):
    """Exception for fatal errors that require immediate attention."""
    pass

class ConfigurationError(AgentError):
    """Exception for configuration-related errors."""
    pass

class CommunicationError(AgentError):
    """Exception for communication-related errors."""
    pass

class ContainerError(AgentError):
    """Exception for container-related errors."""
    pass

class TaskError(AgentError):
    """Exception for task-related errors."""
    pass

class ValidationError(AgentError):
    """Exception for validation-related errors."""
    pass

class ResourceError(AgentError):
    """Exception for resource-related errors."""
    pass

class SecurityError(AgentError):
    """Exception for security-related errors."""
    pass 