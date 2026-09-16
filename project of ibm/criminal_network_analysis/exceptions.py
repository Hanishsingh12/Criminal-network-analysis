"""
exceptions.py
=============
Custom exception classes for the Criminal Network Analysis System.

Each exception has a clear name so that error messages are easy to understand.
All data used in this system is fictional/synthetic for educational purposes only.
"""


class EntityNotFoundError(Exception):
    """Raised when an entity ID does not exist in the network."""
    pass


class DuplicateEntityError(Exception):
    """Raised when trying to add an entity whose ID already exists."""
    pass


class DuplicateRelationshipError(Exception):
    """Raised when the exact same directed relationship already exists."""
    pass


class InvalidRelationshipTypeError(Exception):
    """Raised when a relationship type is not one of the four allowed values."""
    pass


class SelfRelationshipError(Exception):
    """Raised when both ends of a relationship point to the same entity."""
    pass


class InvalidDateFormatError(Exception):
    """Raised when a date string does not match the YYYY-MM-DD format."""
    pass


class EmptyFieldError(Exception):
    """Raised when a required field is blank or contains only whitespace."""
    pass


class IncidentLinkError(Exception):
    """Raised when an incident has no linked entity IDs."""
    pass
