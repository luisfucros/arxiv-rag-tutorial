import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from exceptions import MetadataFetchingException, PipelineException
from arxiv_lib.repositories.paper import PaperRepository
from arxiv_lib.schemas import PaperCreate
from schemas.pdf_parser.models import PdfContent
from arxiv_lib.arxiv.client import ArxivClient
from arxiv_lib.config import Settings
from arxiv_lib.exceptions import EntityNotFound
from services.pdf_parser.parser import PDFParserService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MetadataFetcher:
    """Service for fetching arXiv papers with PDF processing and database storage."""

    def __init__(
        self,
        arxiv_client: ArxivClient,
        pdf_parser: PDFParserService,
        pdf_cache_dir: Optional[Path] = None,
        settings: Optional[Settings] = None,
    ):
        """Initialize metadata fetcher with services and settings.

        :param arxiv_client: Client for arXiv API operations
        :param pdf_parser: Service for parsing PDF documents
        :param pdf_cache_dir: Directory for caching downloaded PDFs
        :param settings: Application settings instance
        :type arxiv_client: ArxivClient
        :type pdf_parser: PDFParserService
        :type pdf_cache_dir: Optional[Path]
        :type max_concurrent_downloads: int
        :type max_concurrent_parsing: int
        :type settings: Optional[Settings]
        """
        from config import settings as config_settings

        self.arxiv_client = arxiv_client
        self.pdf_parser = pdf_parser
        self.pdf_cache_dir = pdf_cache_dir or self.arxiv_client.pdf_cache_dir
        self.settings = settings or config_settings

    def fetch_and_process_papers(
        self,
        paper_ids: List[str],
        process_pdfs: bool = True,
        store_to_db: bool = True,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:

        if store_to_db is True and db_session is None:
            raise PipelineException("db_session is required when store_to_db=True")

        repo = PaperRepository(db_session) if store_to_db is True and db_session is not None else None

        results: Dict[str, Any] = {
            "requested": len(paper_ids),
            "fetched": 0,
            "processed": 0,
            "stored": 0,
            "skipped_papers": [],
            "errors": [],
            "papers": [],
        }

        for arxiv_id in paper_ids:
            try:
                existing_paper = repo.get_by_arxiv_id(arxiv_id) if repo is not None else None
                if existing_paper:
                    results["skipped_papers"].append({
                        "arxiv_id": arxiv_id,
                        "reason": "already_processed",
                        "id": str(existing_paper.id),
                    })
                    logger.info(f"Paper already stored: {arxiv_id}")
                else:
                    try:
                        pdf_path, arxiv_paper = self.arxiv_client.get_by_id_and_download(
                            arxiv_id=arxiv_id,
                            download_pdf=process_pdfs,
                        )
                        if pdf_path is None and arxiv_paper is None:
                            raise MetadataFetchingException(f"Paper not found: {arxiv_id}")
                    except EntityNotFound:
                        results["skipped_papers"].append({
                            "arxiv_id": arxiv_id,
                            "reason": "paper_not_found",
                            "id": None,
                        })
                        logger.error(f"Paper not found: {arxiv_id}")
                        continue

                    logger.info(f"Paper fetched: {arxiv_id}")
                    results["fetched"] += 1

                    paper_dict = {
                        "arxiv_id": str(arxiv_id),
                        "title": arxiv_paper.title,
                        "authors": arxiv_paper.authors,
                        "abstract": arxiv_paper.abstract,
                        "categories": arxiv_paper.categories,
                        "published_date": arxiv_paper.published_date,
                        "pdf_url": arxiv_paper.pdf_url,
                        "pdf_processed": False,
                    }

                    if process_pdfs and pdf_path.exists():
                        try:
                            pdf_content = self.pdf_parser.parse_pdf(pdf_path)

                            if pdf_content:
                                paper_dict.update({
                                    "raw_text": pdf_content.raw_text,
                                    "sections": [s.model_dump() for s in pdf_content.sections],
                                    "parser_used": pdf_content.parser_used.value,
                                    "parser_metadata": pdf_content.metadata,
                                    "pdf_processed": True,
                                    "pdf_processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                })
                                logger.info(f"PDF processed: {arxiv_id}")
                                results["processed"] += 1

                        except Exception as e:
                            logger.exception(f"PDF parsing failed for {arxiv_id}")
                            results["errors"].append(
                                {"arxiv_id": arxiv_id, "stage": "pdf_parsing", "error": str(e)}
                            )

                    paper_create = PaperCreate(**paper_dict)
                    results["papers"].append(paper_dict)
                    if store_to_db is True and repo is not None:
                        repo.upsert(paper_create)
                        logger.info(f"Paper stored: {arxiv_id}")
                        results["stored"] += 1

            except Exception as e:
                logger.exception(f"Failed processing {arxiv_id}: {str(e)}")
                results["errors"].append(
                    {"arxiv_id": arxiv_id, "stage": "fetch/store", "error": str(e)}
                )

        self.arxiv_client.clear_cache()
        logger.info("Cache cleaned")

        return results
