import asyncio
import logging
import re
import tempfile
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

import nltk
import pdfplumber
import requests
from docx import Document
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer

from app.utils.skills_master import extract_skills_from_text

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(
    r"https?://[^\s\]\)\"\'<>]+|"
    r"(?:www\.)?linkedin\.com/in/[^\s\]\)\"\'<>]+|"
    r"(?:www\.)?github\.com/[^\s\]\)\"\'<>]+",
    re.IGNORECASE,
)

EXPERIENCE_KEYWORDS_MASTER: list[str] = [
    "senior",
    "junior",
    "lead",
    "manager",
    "director",
    "architect",
    "engineer",
    "developer",
    "intern",
    "internship",
    "consultant",
    "analyst",
    "specialist",
    "principal",
    "staff",
    "head of",
    "vice president",
    "vp",
    "years of experience",
    "yoe",
    "full-time",
    "contract",
    "remote",
    "onsite",
    "hybrid",
    "responsible for",
    "led",
    "managed",
    "developed",
    "implemented",
    "designed",
    "built",
    "delivered",
    "maintained",
    "optimized",
    "scaled",
    "mentored",
    "cross-functional",
    "stakeholder",
    "roadmap",
    "production",
    "enterprise",
    "startup",
]

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
DOWNLOAD_TIMEOUT_SECONDS = 30

_nltk_initialized = False


def _ensure_nltk_resources() -> None:
    global _nltk_initialized
    if _nltk_initialized:
        return
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)
    _nltk_initialized = True


class ResumeParseError(Exception):
    """Raised when resume download or parsing fails."""


class ParsedResumeProfile(TypedDict):
    raw_text: str
    emails: list[str]
    links: list[str]
    skills: list[str]
    experience_keywords: list[str]
    resume_url: str


def _detect_extension(resume_url: str, filename: str) -> str:
    path = Path(filename).suffix.lower()
    if path in SUPPORTED_EXTENSIONS:
        return path

    parsed = urlparse(resume_url)
    url_suffix = Path(parsed.path).suffix.lower()
    if url_suffix in SUPPORTED_EXTENSIONS:
        return url_suffix

    raise ResumeParseError(
        f"Unsupported resume format. Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


def _write_temp_file(file_data: bytes, suffix: str) -> Path:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_file.name)
    try:
        temp_file.write(file_data)
        temp_file.close()
    except OSError as exc:
        temp_path.unlink(missing_ok=True)
        raise ResumeParseError("Failed to write temporary resume file") from exc
    return temp_path


def _download_resume_sync(resume_url: str, suffix: str) -> Path:
    try:
        response = requests.get(resume_url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Failed to download resume from Cloudinary")
        raise ResumeParseError("Failed to download resume for parsing") from exc

    return _write_temp_file(response.content, suffix)


def _parse_resume_bytes_sync(
    file_data: bytes,
    filename: str,
    resume_url: str,
) -> ParsedResumeProfile:
    extension = _detect_extension(resume_url, filename)
    temp_path: Path | None = None

    try:
        temp_path = _write_temp_file(file_data, extension)
        return _build_parsed_profile(temp_path, extension, resume_url, filename)
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
                logger.debug("Temporary resume file removed: %s", temp_path)
            except OSError:
                logger.warning("Failed to remove temporary resume file: %s", temp_path)


def _build_parsed_profile(
    temp_path: Path,
    extension: str,
    resume_url: str,
    filename: str,
) -> ParsedResumeProfile:
    raw_text = _extract_raw_text(temp_path, extension)

    if not raw_text:
        logger.warning("No text extracted from resume: %s", filename)

    emails = _extract_emails(raw_text)
    links = _extract_links(raw_text)
    skills = extract_skills_from_text(raw_text)
    experience_keywords = _extract_experience_keywords(raw_text, skills)

    logger.info(
        "Resume parsed: emails=%d links=%d skills=%d experience_keywords=%d",
        len(emails),
        len(links),
        len(skills),
        len(experience_keywords),
    )

    return ParsedResumeProfile(
        raw_text=raw_text,
        emails=emails,
        links=links,
        skills=skills,
        experience_keywords=experience_keywords,
        resume_url=resume_url,
    )


def _extract_text_from_pdf(file_path: Path) -> str:
    try:
        with pdfplumber.open(file_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()
    except Exception as exc:
        logger.exception("PDF text extraction failed: %s", file_path)
        raise ResumeParseError("Failed to extract text from PDF resume") from exc


def _extract_text_from_docx(file_path: Path) -> str:
    try:
        document = Document(file_path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        return "\n".join(paragraphs).strip()
    except Exception as exc:
        logger.exception("DOCX text extraction failed: %s", file_path)
        raise ResumeParseError("Failed to extract text from DOCX resume") from exc


def _extract_raw_text(file_path: Path, extension: str) -> str:
    if extension == ".pdf":
        return _extract_text_from_pdf(file_path)
    if extension == ".docx":
        return _extract_text_from_docx(file_path)
    raise ResumeParseError(f"Unsupported file extension: {extension}")


def _extract_emails(text: str) -> list[str]:
    return sorted({match.group(0).lower() for match in EMAIL_PATTERN.finditer(text)})


def _normalize_link(link: str) -> str:
    cleaned = link.rstrip(".,;)")
    if cleaned.lower().startswith(("linkedin.com", "github.com", "www.")):
        return f"https://{cleaned}" if not cleaned.startswith("http") else cleaned
    return cleaned


def _extract_links(text: str) -> list[str]:
    found = {_normalize_link(match.group(0)) for match in URL_PATTERN.finditer(text)}
    return sorted(found)


def _extract_experience_keywords_from_master(text: str) -> list[str]:
    text_lower = text.lower()
    found: list[str] = []
    for keyword in EXPERIENCE_KEYWORDS_MASTER:
        if keyword in text_lower and keyword not in found:
            found.append(keyword)
    return found


def _extract_experience_keywords_from_tfidf(text: str) -> list[str]:
    if not text.strip():
        return []

    _ensure_nltk_resources()

    try:
        vectorizer = TfidfVectorizer(
            max_features=12,
            stop_words=list(stopwords.words("english")),
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9+#./-]{1,}\b",
        )
        matrix = vectorizer.fit_transform([text])
        scores = matrix.toarray()[0]
        terms = vectorizer.get_feature_names_out()
        ranked = sorted(zip(terms, scores), key=lambda item: item[1], reverse=True)
        return [term for term, score in ranked if score > 0]
    except Exception:
        logger.warning("TF-IDF experience keyword extraction failed; using master list only")
        return []


def _extract_experience_keywords(text: str, skills: list[str]) -> list[str]:
    skill_terms = {skill.lower() for skill in skills}
    master_matches = _extract_experience_keywords_from_master(text)
    tfidf_matches = _extract_experience_keywords_from_tfidf(text)

    combined: list[str] = []
    seen: set[str] = set()
    for keyword in master_matches + tfidf_matches:
        normalized = keyword.lower().strip()
        if normalized in seen or normalized in skill_terms:
            continue
        seen.add(normalized)
        combined.append(keyword)

    return combined[:25]


def _parse_resume_sync(resume_url: str, filename: str) -> ParsedResumeProfile:
    extension = _detect_extension(resume_url, filename)
    temp_path: Path | None = None

    try:
        temp_path = _download_resume_sync(resume_url, extension)
        return _build_parsed_profile(temp_path, extension, resume_url, filename)
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
                logger.debug("Temporary resume file removed: %s", temp_path)
            except OSError:
                logger.warning("Failed to remove temporary resume file: %s", temp_path)


async def parse_resume_from_bytes(
    file_data: bytes,
    filename: str,
    resume_url: str,
) -> ParsedResumeProfile:
    """Parse resume bytes locally (avoids re-downloading from Cloudinary)."""
    if not file_data:
        raise ResumeParseError("Resume file is empty")
    if not resume_url.strip():
        raise ResumeParseError("resume_url is required")

    return await asyncio.to_thread(
        _parse_resume_bytes_sync,
        file_data,
        filename,
        resume_url,
    )


async def parse_resume_from_url(
    resume_url: str,
    filename: str,
) -> ParsedResumeProfile:
    """Download a resume from Cloudinary, parse it, and return structured profile data."""
    if not resume_url.strip():
        raise ResumeParseError("resume_url is required")

    return await asyncio.to_thread(_parse_resume_sync, resume_url, filename)
