import hashlib
import logging
from datetime import datetime
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ai.rag import add_chunks, delete_by_source
from config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


def _read_file(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except ImportError:
            pass
        try:
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            raise ImportError("Install pdfplumber or PyPDF2 to read PDF files")
    if suffix == ".docx":
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            raise ImportError("Install python-docx to read DOCX files")
    raise ValueError(f"Unsupported file type: {suffix}")


def index_file(file_path: str, source_name: str | None = None) -> int:
    if source_name is None:
        source_name = Path(file_path).name
    delete_by_source(source_name)

    text = _read_file(file_path)
    if not text.strip():
        logger.warning("Empty file: %s", file_path)
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)

    date_str = datetime.utcnow().isoformat()
    ids = [
        hashlib.md5(f"{source_name}_{i}_{chunk[:50]}".encode()).hexdigest()
        for i, chunk in enumerate(chunks)
    ]
    metadatas = [{"source": source_name, "date": date_str, "chunk_index": i} for i, _ in enumerate(chunks)]

    add_chunks(chunks, metadatas, ids)
    logger.info("Indexed %d chunks from %s", len(chunks), source_name)
    return len(chunks)


def index_text(text: str, source_name: str) -> int:
    delete_by_source(source_name)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_text(text)
    if not chunks:
        return 0
    date_str = datetime.utcnow().isoformat()
    ids = [
        hashlib.md5(f"{source_name}_{i}".encode()).hexdigest()
        for i in range(len(chunks))
    ]
    metadatas = [{"source": source_name, "date": date_str, "chunk_index": i} for i in range(len(chunks))]
    add_chunks(chunks, metadatas, ids)
    return len(chunks)
