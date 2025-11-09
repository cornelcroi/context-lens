"""Tests for comprehensive error handling module."""

import pytest

from context_lens.errors import (
    DatabaseError,
    EmbeddingError,
    ErrorCategory,
    FileValidationError,
    KnowledgeBaseError,
    ParameterValidationError,
    create_error_response,
    validate_file_path,
    validate_limit_parameter,
    validate_offset_parameter,
    validate_query_parameter,
)


class TestErrorCategories:
    """Test error category enumeration."""

    def test_error_categories_exist(self):
        """Test that all expected error categories are defined."""
        expected_categories = [
            "FILE_NOT_FOUND",
            "FILE_ACCESS_DENIED",
            "FILE_TOO_LARGE",
            "UNSUPPORTED_FILE_TYPE",
            "INVALID_PARAMETER",
            "DATABASE_OPERATION_ERROR",
            "EMBEDDING_GENERATION_ERROR",
            "SERVICE_NOT_INITIALIZED",
        ]

        for category in expected_categories:
            assert hasattr(ErrorCategory, category)

    def test_error_category_values(self):
        """Test that error categories have correct string values."""
        assert ErrorCategory.FILE_NOT_FOUND.value == "file_not_found"
        assert ErrorCategory.INVALID_PARAMETER.value == "invalid_parameter"
        assert ErrorCategory.DATABASE_OPERATION_ERROR.value == "database_operation_error"


class TestKnowledgeBaseError:
    """Test base KnowledgeBaseError class."""

    def test_error_creation(self):
        """Test creating a basic error."""
        error = KnowledgeBaseError(
            message="Test error",
            error_category=ErrorCategory.INTERNAL_ERROR,
            details={"key": "value"},
        )

        assert error.message == "Test error"
        assert error.error_category == ErrorCategory.INTERNAL_ERROR
        assert error.details == {"key": "value"}

    def test_error_to_dict(self):
        """Test converting error to dictionary."""
        error = KnowledgeBaseError(
            message="Test error",
            error_category=ErrorCategory.FILE_NOT_FOUND,
            details={"file_path": "/test/path"},
        )

        error_dict = error.to_dict()

        assert error_dict["success"] is False
        assert error_dict["error_type"] == "file_not_found"
        assert error_dict["error_message"] == "Test error"
        assert error_dict["error_details"]["file_path"] == "/test/path"

    def test_error_with_original_exception(self):
        """Test error with original exception."""
        original = ValueError("Original error")
        error = KnowledgeBaseError(
            message="Wrapped error",
            error_category=ErrorCategory.VALIDATION_ERROR,
            original_error=original,
        )

        error_dict = error.to_dict()

        assert "original_error" in error_dict["error_details"]
        assert error_dict["error_details"]["original_error"] == "Original error"
        assert error_dict["error_details"]["original_error_type"] == "ValueError"


class TestSpecializedErrors:
    """Test specialized error classes."""

    def test_file_validation_error(self):
        """Test FileValidationError."""
        error = FileValidationError(message="File not found", file_path="/test/file.txt")

        assert error.message == "File not found"
        assert error.error_category == ErrorCategory.VALIDATION_ERROR
        assert error.details["file_path"] == "/test/file.txt"

    def test_parameter_validation_error(self):
        """Test ParameterValidationError."""
        error = ParameterValidationError(
            message="Invalid parameter", parameter_name="limit", parameter_value=1000
        )

        assert error.message == "Invalid parameter"
        assert error.error_category == ErrorCategory.INVALID_PARAMETER
        assert error.details["parameter_name"] == "limit"
        assert error.details["parameter_value"] == 1000

    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError(
            message="Database operation failed", operation="insert", details={"table": "documents"}
        )

        assert error.message == "Database operation failed"
        assert error.error_category == ErrorCategory.DATABASE_OPERATION_ERROR
        assert error.details["operation"] == "insert"
        assert error.details["table"] == "documents"

    def test_embedding_error(self):
        """Test EmbeddingError."""
        error = EmbeddingError(
            message="Failed to generate embedding", details={"model": "test-model"}
        )

        assert error.message == "Failed to generate embedding"
        assert error.error_category == ErrorCategory.EMBEDDING_GENERATION_ERROR
        assert error.details["model"] == "test-model"


class TestCreateErrorResponse:
    """Test create_error_response utility function."""

    def test_create_error_from_knowledge_base_error(self):
        """Test creating response from KnowledgeBaseError."""
        error = KnowledgeBaseError(
            message="Test error", error_category=ErrorCategory.FILE_NOT_FOUND
        )

        response = create_error_response(error)

        assert response["success"] is False
        assert response["error_type"] == "file_not_found"
        assert response["error_message"] == "Test error"

    def test_create_error_from_generic_exception(self):
        """Test creating response from generic exception."""
        error = ValueError("Generic error")

        response = create_error_response(error, context={"operation": "test"})

        assert response["success"] is False
        assert response["error_type"] == "internal_error"
        assert response["error_message"] == "Generic error"
        assert response["error_details"]["operation"] == "test"
        assert response["error_details"]["error_type"] == "ValueError"

    def test_create_error_with_default_message(self):
        """Test creating response with default message."""
        error = Exception()  # Empty exception

        response = create_error_response(error, default_message="Default message")

        assert response["error_message"] == "Default message"


class TestFilePathValidation:
    """Test file path validation."""

    def test_valid_file_path(self):
        """Test validation of valid file path."""
        # Should not raise exception
        validate_file_path("/valid/path/to/file.txt")
        validate_file_path("relative/path/file.py")

    def test_empty_file_path(self):
        """Test validation of empty file path."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_file_path("")

        assert "cannot be empty" in str(exc_info.value)

    def test_whitespace_only_file_path(self):
        """Test validation of whitespace-only file path."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_file_path("   ")

        assert "whitespace only" in str(exc_info.value)

    def test_non_string_file_path(self):
        """Test validation of non-string file path."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_file_path(123)

        assert "must be a string" in str(exc_info.value)

    def test_file_path_too_long(self):
        """Test validation of excessively long file path."""
        long_path = "a" * 5000

        with pytest.raises(ParameterValidationError) as exc_info:
            validate_file_path(long_path)

        assert "too long" in str(exc_info.value)


class TestQueryParameterValidation:
    """Test query parameter validation."""

    def test_valid_query(self):
        """Test validation of valid query."""
        validate_query_parameter("test query")
        validate_query_parameter("a" * 100)

    def test_empty_query(self):
        """Test validation of empty query."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_query_parameter("")

        assert "cannot be empty" in str(exc_info.value)

    def test_whitespace_only_query(self):
        """Test validation of whitespace-only query."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_query_parameter("   ")

        assert "whitespace only" in str(exc_info.value)

    def test_query_too_long(self):
        """Test validation of excessively long query."""
        long_query = "a" * 11000

        with pytest.raises(ParameterValidationError) as exc_info:
            validate_query_parameter(long_query)

        assert "too long" in str(exc_info.value)

    def test_non_string_query(self):
        """Test validation of non-string query."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_query_parameter(123)

        assert "must be a string" in str(exc_info.value)


class TestLimitParameterValidation:
    """Test limit parameter validation."""

    def test_valid_limit(self):
        """Test validation of valid limit values."""
        validate_limit_parameter(10)
        validate_limit_parameter(100)
        validate_limit_parameter(None)  # None is valid

    def test_limit_too_small(self):
        """Test validation of limit below minimum."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_limit_parameter(0)

        assert "at least" in str(exc_info.value)

    def test_limit_too_large(self):
        """Test validation of limit above maximum."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_limit_parameter(2000)

        assert "cannot exceed" in str(exc_info.value)

    def test_non_integer_limit(self):
        """Test validation of non-integer limit."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_limit_parameter("10")

        assert "must be an integer" in str(exc_info.value)

    def test_custom_limit_range(self):
        """Test validation with custom min/max values."""
        validate_limit_parameter(5, min_value=1, max_value=10)

        with pytest.raises(ParameterValidationError):
            validate_limit_parameter(15, min_value=1, max_value=10)


class TestOffsetParameterValidation:
    """Test offset parameter validation."""

    def test_valid_offset(self):
        """Test validation of valid offset values."""
        validate_offset_parameter(0)
        validate_offset_parameter(100)
        validate_offset_parameter(1000)

    def test_negative_offset(self):
        """Test validation of negative offset."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_offset_parameter(-1)

        assert "cannot be negative" in str(exc_info.value)

    def test_offset_too_large(self):
        """Test validation of excessively large offset."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_offset_parameter(200000)

        assert "too large" in str(exc_info.value)

    def test_non_integer_offset(self):
        """Test validation of non-integer offset."""
        with pytest.raises(ParameterValidationError) as exc_info:
            validate_offset_parameter("10")

        assert "must be an integer" in str(exc_info.value)


class TestErrorLogging:
    """Test error logging functionality."""

    def test_log_error_method(self, caplog):
        """Test that log_error method logs correctly."""
        import logging

        error = KnowledgeBaseError(
            message="Test error for logging",
            error_category=ErrorCategory.VALIDATION_ERROR,
            details={"test": "data"},
        )

        with caplog.at_level(logging.ERROR):
            error.log_error()

        assert "Test error for logging" in caplog.text
        assert "validation_error" in caplog.text
