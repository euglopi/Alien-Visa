from typing import Literal

from pydantic import BaseModel


class ParsedResume(BaseModel):
    """Model representing a parsed resume."""

    filename: str
    raw_text: str
    file_type: Literal["pdf", "docx"]
    parse_success: bool
    error_message: str | None = None
