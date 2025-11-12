import io

from PyPDF2 import PdfReader


class PDFParser:
    """Service for parsing resume files."""

    def extract_from_pdf(self, file_field):
        """Extract text from a PDF file."""
        try:
            # Read the file from Django's FileField
            file_content = file_field.read()
            pdf_file = io.BytesIO(file_content)

            # Parse PDF
            reader = PdfReader(pdf_file)
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n".join(text_parts)

            if not full_text.strip():
                raise ValueError("PDF appears to be empty or contains only images")

            return full_text

        except Exception as e:
            raise Exception(f"Failed to parse PDF: {e}")

    def extract_from_text(self, file_field):
        """Extract text from a plain text file."""
        try:
            file_content = file_field.read()

            # Try different encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = file_content.decode(encoding)
                    return text
                except UnicodeDecodeError:
                    continue

            raise ValueError("Could not decode text file with any known encoding")

        except Exception as e:
            raise Exception(f"Failed to parse text file: {e}")

    def extract_from_docx(self, file_field):
        """Extract text from a DOCX file."""
        try:
            import docx

            file_content = file_field.read()
            doc_file = io.BytesIO(file_content)

            doc = docx.Document(doc_file)
            text_parts = []

            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_parts.append(paragraph.text)

            full_text = "\n".join(text_parts)

            if not full_text.strip():
                raise ValueError("DOCX appears to be empty")

            return full_text

        except ImportError:
            raise Exception(
                "python-docx package is required for DOCX files. "
                "Install with: pip install python-docx"
            )
        except Exception as e:
            raise Exception(f"Failed to parse DOCX: {e}")

