import shutil
from datetime import datetime, timedelta
from functools import cached_property
from pathlib import Path
from typing import List, Optional, Tuple

import arxiv
from ..config import ArxivSettings
from ..schemas import ArxivPaper
from arxiv import HTTPError
from ..exceptions import EntityNotFound
from .errors import handle_errors


class ArxivClient:
    """Client for searching and downloading papers from arXiv.

    Handles paper search, retrieval, and PDF downloads with caching.
    Provides rate limiting and configurable pagination.
    """
    # Default configuration constants
    DEFAULT_PAGE_SIZE = 10
    DEFAULT_DELAY_SECONDS = 3
    DEFAULT_NUM_RETRIES = 3

    def __init__(self, settings: ArxivSettings,
                 page_size: int = DEFAULT_PAGE_SIZE,
                 delay_seconds: int = DEFAULT_DELAY_SECONDS,
                 num_retries: int = DEFAULT_NUM_RETRIES) -> None:
        """
        Initialize a reusable arxiv.Client.
        You can tune page size and delay to control pagination & rate limiting.

        Args:
            settings: ArxivSettings configuration object
            page_size: Number of results per page
            delay_seconds: Delay between requests in seconds
            num_retries: Number of retries for failed requests

        Raises:
            ValueError: If settings is None
        """
        if settings is None:
            raise ValueError("settings cannot be None")

        self._settings = settings

        # Validate cache directory is writable
        cache_path = Path(settings.pdf_cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        if not cache_path.is_dir():
            raise ValueError(f"pdf_cache_dir must be a directory: {cache_path}")

        self.client = arxiv.Client(
            page_size=page_size,
            delay_seconds=delay_seconds,
            num_retries=num_retries
        )

    @cached_property
    def pdf_cache_dir(self) -> Path:
        """PDF cache directory."""
        cache_dir = Path(self._settings.pdf_cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _get_pdf_path(self, arxiv_id: str) -> Path:
        """
        Get the local path for a PDF file.

        Args:
            arxiv_id: arXiv paper ID

        Returns:
            Path object for the PDF file
        """
        safe_filename = arxiv_id.replace("/", "_") + ".pdf"
        return self.pdf_cache_dir / safe_filename

    def _is_pdf_cached(self, arxiv_id: str) -> bool:
        """
        Check if a PDF is already cached locally.

        Args:
            arxiv_id: arXiv paper ID

        Returns:
            True if PDF exists in cache, False otherwise
        """
        pdf_path = self._get_pdf_path(arxiv_id)
        return pdf_path.exists() and pdf_path.is_file()

    @handle_errors
    def search_papers(
        self,
        query: str,
        max_results: int = 10,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending,
    ) -> List[ArxivPaper]:
        """
        Search arXiv papers matching a query string.
        Returns a list of ArxivPaper objects up to max_results.

        Raises:
            HTTPError: If the arXiv API request fails
        """
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        papers = [ArxivPaper(
                arxiv_id=paper.entry_id,
                title=paper.title,
                authors=[author.name for author in paper.authors],
                abstract=paper.summary,
                categories=paper.categories,
                published_date=paper.published,
                pdf_url=paper.pdf_url,
            ) for paper in list(self.client.results(search))]

        return papers

    @handle_errors
    def get_by_id(self, arxiv_id: str) -> Tuple[Optional[ArxivPaper], Optional[arxiv.Result]]:
        """
        Retrieve a single paper by its arXiv ID (e.g., "2101.12345v1").

        Args:
            arxiv_id: The arXiv ID to search for

        Returns:
            Tuple of (ArxivPaper, arxiv.Result) or (None, None) if not found

        Raises:
            HTTPError: If the arXiv API request fails
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id], max_results=1)
            for result in self.client.results(search):
                paper = ArxivPaper(
                    arxiv_id=result.entry_id,
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    categories=result.categories,
                    published_date=result.published,
                    pdf_url=result.pdf_url,
                )
                return paper, result
        except HTTPError:
            raise EntityNotFound(
                "Paper with id: '%s' not found" % arxiv_id
            )

        return None, None

    @handle_errors
    def download_pdf(
        self,
        arxiv_result: arxiv.Result,
        filename: Optional[str] = None,
        force_download: bool = False,
    ) -> str:
        """
        Download the PDF of a result.

        Args:
            arxiv_result: The arXiv result object
            filename: Optional custom filename for the PDF
            force_download: If True, re-download even if cached (default: False)

        Returns:
            Path of the saved file

        Raises:
            FileNotFoundError: If PDF not found after download
            IOError: If PDF download or disk write fails
        """
        # Check cache first
        if not force_download and self._is_pdf_cached(arxiv_result.entry_id):
            cached_path = self._get_pdf_path(arxiv_result.entry_id)
            return str(cached_path)

        if filename is None:
            pdf_path = arxiv_result.download_pdf(dirpath=str(self.pdf_cache_dir))
        else:
            pdf_path = arxiv_result.download_pdf(dirpath=str(self.pdf_cache_dir), filename=filename)

        # Verify file exists
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found at {pdf_path} after download")

        return pdf_path

    @handle_errors
    def get_by_id_and_download(
        self,
        arxiv_id: str,
        download_pdf: bool = True,
        force_download: bool = False,
    ) -> Tuple[Optional[Path], Optional[ArxivPaper]]:
        """
        Retrieve a paper by ID and optionally download its PDF.

        Args:
            arxiv_id: The arXiv ID to search for
            download_pdf: Whether to download the PDF (default: True)
            force_download: If True, re-download even if cached (default: False)

        Returns:
            Tuple of (pdf_path, paper) where pdf_path is None if not downloaded

        Raises:
            HTTPError: If the arXiv API request fails
            FileNotFoundError: If PDF download fails
        """
        paper, result = self.get_by_id(arxiv_id)
        if result is None or paper is None:
            return None, None

        if download_pdf:
            pdf_path = self.download_pdf(result, force_download=force_download)
            return Path(pdf_path), paper
        else:
            return None, paper

    @handle_errors
    def clear_cache(self) -> None:
        """
        Remove all cached PDFs.

        Raises:
            OSError: If cache directory cannot be removed
        """
        if self.pdf_cache_dir.exists():
            shutil.rmtree(self.pdf_cache_dir)
            self.pdf_cache_dir.mkdir(parents=True, exist_ok=True)

    @handle_errors
    def cleanup_old_pdfs(self, days: int = 1) -> int:
        """
        Remove cached PDFs older than the specified number of days.

        Args:
            days: Number of days to keep (default: 1)

        Returns:
            Number of files deleted

        Raises:
            ValueError: If days is negative
        """
        if days < 0:
            raise ValueError("days cannot be negative")

        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for pdf_file in self.pdf_cache_dir.glob("*.pdf"):
            file_time = datetime.fromtimestamp(pdf_file.stat().st_mtime)
            if file_time < cutoff_time:
                pdf_file.unlink()
                deleted_count += 1

        return deleted_count

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit. Cleanup if needed."""
        return False
