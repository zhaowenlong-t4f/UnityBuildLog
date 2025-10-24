"""Basic exceptions for the log reader module."""

class LogReaderError(Exception):
    """Base exception for all log reader errors."""
    pass

class FileFormatError(LogReaderError):
    """Raised when the file format is invalid or unsupported."""
    pass

class ReadError(LogReaderError):
    """Raised when there is an error reading the file."""
    pass

class ConfigError(LogReaderError):
    """Raised when there is a configuration error."""
    pass