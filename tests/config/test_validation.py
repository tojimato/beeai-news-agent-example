"""
Tests for data validation models.
"""

import pytest
from pydantic import ValidationError

from src.config.validation import (
    RecipientModel,
    RecipientsListModel,
    PipelineInputModel
)


class TestRecipientModel:
    """Test RecipientModel validation."""
    
    def test_valid_recipient(self) -> None:
        """Test valid recipient data."""
        data = {
            "email": "user@example.com",
            "profession": "solo_developer",
            "name": "John Doe",
            "hour": 9,
            "minute": 0,
            "language": "en"
        }
        recipient = RecipientModel(**data)
        assert recipient.email == "user@example.com"
        assert recipient.language == "en"
    
    def test_default_language(self) -> None:
        """Test default language is Turkish."""
        data = {
            "email": "user@example.com",
            "profession": "solo_developer",
            "name": "John Doe",
            "hour": 9,
            "minute": 0
        }
        recipient = RecipientModel(**data)
        assert recipient.language == "tr"
    
    def test_invalid_email(self) -> None:
        """Test invalid email format."""
        data = {
            "email": "not-an-email",
            "profession": "solo_developer",
            "name": "John Doe",
            "hour": 9,
            "minute": 0
        }
        with pytest.raises(ValidationError):
            RecipientModel(**data)
    
    def test_invalid_hour(self) -> None:
        """Test hour validation."""
        data = {
            "email": "user@example.com",
            "profession": "solo_developer",
            "name": "John Doe",
            "hour": 25,
            "minute": 0
        }
        with pytest.raises(ValidationError) as exc_info:
            RecipientModel(**data)
        assert "hour must be 0-23" in str(exc_info.value)
    
    def test_invalid_minute(self) -> None:
        """Test minute validation."""
        data = {
            "email": "user@example.com",
            "profession": "solo_developer",
            "name": "John Doe",
            "hour": 9,
            "minute": 65
        }
        with pytest.raises(ValidationError) as exc_info:
            RecipientModel(**data)
        assert "minute must be 0-59" in str(exc_info.value)
    
    def test_invalid_language(self) -> None:
        """Test language must be tr or en."""
        data = {
            "email": "user@example.com",
            "profession": "solo_developer",
            "name": "John Doe",
            "hour": 9,
            "minute": 0,
            "language": "fr"
        }
        with pytest.raises(ValidationError):
            RecipientModel(**data)
    
    def test_empty_profession(self) -> None:
        """Test profession cannot be empty."""
        data = {
            "email": "user@example.com",
            "profession": "",
            "name": "John Doe",
            "hour": 9,
            "minute": 0
        }
        with pytest.raises(ValidationError):
            RecipientModel(**data)
    
    def test_whitespace_stripped(self) -> None:
        """Test whitespace is stripped from string fields."""
        data = {
            "email": "user@example.com",
            "profession": "  solo_developer  ",
            "name": "  John Doe  ",
            "hour": 9,
            "minute": 0
        }
        recipient = RecipientModel(**data)
        assert recipient.profession == "solo_developer"
        assert recipient.name == "John Doe"


class TestRecipientsListModel:
    """Test RecipientsListModel validation."""
    
    def test_valid_recipients_list(self) -> None:
        """Test valid recipients list."""
        data = [
            {
                "email": "user1@example.com",
                "profession": "solo_developer",
                "name": "User 1",
                "hour": 9,
                "minute": 0
            },
            {
                "email": "user2@example.com",
                "profession": "lawyer",
                "name": "User 2",
                "hour": 10,
                "minute": 30,
                "language": "en"
            }
        ]
        recipients = RecipientsListModel.from_list(data)
        assert len(recipients.recipients) == 2
        assert recipients.recipients[0].email == "user1@example.com"
    
    def test_invalid_recipient_in_list(self) -> None:
        """Test invalid recipient in list fails entire validation."""
        data = [
            {
                "email": "user1@example.com",
                "profession": "solo_developer",
                "name": "User 1",
                "hour": 9,
                "minute": 0
            },
            {
                "email": "invalid-email",
                "profession": "lawyer",
                "name": "User 2",
                "hour": 10,
                "minute": 30
            }
        ]
        with pytest.raises(ValidationError):
            RecipientsListModel.from_list(data)


class TestPipelineInputModel:
    """Test PipelineInputModel validation."""
    
    def test_valid_pipeline_input(self) -> None:
        """Test valid pipeline input."""
        data = {
            "profession": "solo_developer",
            "language": "en"
        }
        model = PipelineInputModel(**data)
        assert model.profession == "solo_developer"
        assert model.language == "en"
    
    def test_default_language(self) -> None:
        """Test default language is Turkish."""
        data = {"profession": "solo_developer"}
        model = PipelineInputModel(**data)
        assert model.language == "tr"
    
    def test_invalid_language(self) -> None:
        """Test language must be tr or en."""
        data = {
            "profession": "solo_developer",
            "language": "de"
        }
        with pytest.raises(ValidationError):
            PipelineInputModel(**data)
    
    def test_empty_profession(self) -> None:
        """Test profession cannot be empty."""
        data = {
            "profession": "",
            "language": "en"
        }
        with pytest.raises(ValidationError):
            PipelineInputModel(**data)
