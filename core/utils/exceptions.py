"""Custom exceptions for the P.E.P.P.E.R. system."""

class PEPPERError(Exception):
    """Base exception for all P.E.P.P.E.R. errors."""
    pass

class TransientError(PEPPERError):
    """Error that may be resolved by retrying."""
    pass

class FatalError(PEPPERError):
    """Error that cannot be resolved by retrying."""
    pass

class AgentError(PEPPERError):
    """Error specific to agent execution."""
    pass

class ConfigurationError(PEPPERError):
    """Error related to configuration issues."""
    pass 