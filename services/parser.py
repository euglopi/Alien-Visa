import base64
import io
import os
from typing import Literal

import fitz  # pymupdf
from docx import Document
from dotenv import load_dotenv
from openai import OpenAI

from models.resume import ParsedResume

# Load environment variables
load_dotenv()


def _get_file_type(filename: str) -> Literal["pdf", "docx"] | None:
    """Determine file type from filename extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "pdf"
    elif lower.endswith(".docx"):
        return "docx"
    return None


def _parse_pdf_with_vision(content: bytes) -> str:
    """Render PDF pages to images and extract text using OpenAI Vision."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Open PDF from bytes
    doc = fitz.open(stream=content, filetype="pdf")

    all_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Render page to image (2x zoom for better quality)
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PNG bytes
        img_bytes = pix.tobytes("png")
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        # Send to OpenAI Vision
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this resume page. Preserve the structure and formatting as much as possible. Return only the extracted text, no commentary.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
        )

        page_text = response.choices[0].message.content
        all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")

    doc.close()

    return "\n\n".join(all_text)


def _parse_docx(content: bytes) -> str:
    """Extract text from DOCX file."""
    doc = Document(io.BytesIO(content))

    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)

    return "\n\n".join(paragraphs)


async def parse_resume(file_content: bytes, filename: str) -> ParsedResume:
    """Parse resume file and extract text.

    Args:
        file_content: Raw bytes of the uploaded file
        filename: Original filename (used to detect file type)

    Returns:
        ParsedResume with extracted text or error message
    """
    file_type = _get_file_type(filename)

    if file_type is None:
        return ParsedResume(
            filename=filename,
            raw_text="",
            file_type="pdf",  # Default, doesn't matter for error case
            parse_success=False,
            error_message=f"Unsupported file type. Please upload a PDF or DOCX file.",
        )

    try:
        if file_type == "pdf":
            raw_text = _parse_pdf_with_vision(file_content)
        else:
            raw_text = _parse_docx(file_content)

        return ParsedResume(
            filename=filename,
            raw_text=raw_text,
            file_type=file_type,
            parse_success=True,
        )

    except Exception as e:
        return ParsedResume(
            filename=filename,
            raw_text="",
            file_type=file_type,
            parse_success=False,
            error_message=str(e),
        )
