
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader


def load_document(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {path}"
        )

    documents = []

    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))

        if reader.is_encrypted:
            raise ValueError(
                "Password-protected PDFs are not supported."
            )

        for page_number, page in enumerate(
            reader.pages, start=1
        ):
            text = page.extract_text() or ""

            if text.strip():
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": path.name,
                            "page": page_number,
                        },
                    )
                )

    elif path.suffix.lower() == ".txt":
        text = path.read_text(
            encoding="utf-8-sig"
        )

        if text.strip():
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "page": None,
                    },
                )
            )

    else:
        raise ValueError(
            "Only PDF and TXT files are supported."
        )

    if not documents:
        raise ValueError(
            "No readable text found in document."
        )

    return documents
