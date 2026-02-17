import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
from typing import Generator

import arxiv

from arxiv_lib.arxiv.client import ArxivClient
from arxiv_lib.config import ArxivSettings
from arxiv_lib.schemas import ArxivPaper
from arxiv_lib.exceptions import EntityNotFound, ServiceNotAvailable
from arxiv import HTTPError


@pytest.fixture
def temp_cache_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for PDF cache."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def arxiv_settings(temp_cache_dir) -> ArxivSettings:
    """Create test ArxivSettings."""
    return ArxivSettings(pdf_cache_dir=str(temp_cache_dir))


@pytest.fixture
def arxiv_client(arxiv_settings: ArxivSettings) -> ArxivClient:
    """Create a test ArxivClient instance."""
    return ArxivClient(arxiv_settings)


class TestArxivClientInitialization:
    """Test ArxivClient initialization."""

    def test_init_with_valid_settings(self, arxiv_settings: ArxivSettings):
        """Test successful initialization with valid settings."""
        client = ArxivClient(arxiv_settings)
        assert client._settings == arxiv_settings
        assert client.client is not None

    def test_init_with_none_settings(self):
        """Test that initialization raises ValueError with None settings."""
        with pytest.raises(ValueError, match="settings cannot be None"):
            ArxivClient(None)

    def test_init_with_custom_page_size(self, arxiv_settings: ArxivSettings):
        """Test initialization with custom page size."""
        client = ArxivClient(arxiv_settings, page_size=20)
        assert client.client.page_size == 20

    def test_init_with_custom_delay_seconds(self, arxiv_settings: ArxivSettings):
        """Test initialization with custom delay seconds."""
        client = ArxivClient(arxiv_settings, delay_seconds=5)
        assert client.client.delay_seconds == 5

    def test_init_with_custom_num_retries(self, arxiv_settings: ArxivSettings):
        """Test initialization with custom num retries."""
        client = ArxivClient(arxiv_settings, num_retries=5)
        assert client.client.num_retries == 5

    def test_init_creates_cache_directory(self, temp_cache_dir: Path):
        """Test that initialization creates cache directory."""
        settings = ArxivSettings(pdf_cache_dir=str(temp_cache_dir / "new_cache"))
        client = ArxivClient(settings)
        assert client.pdf_cache_dir.exists()
        assert client.pdf_cache_dir.is_dir()


class TestPdfCacheDir:
    """Test pdf_cache_dir property."""

    def test_pdf_cache_dir_property(self, arxiv_client: ArxivClient, temp_cache_dir: Path):
        """Test pdf_cache_dir property returns correct path."""
        assert arxiv_client.pdf_cache_dir == temp_cache_dir

    def test_pdf_cache_dir_creates_directory(self, arxiv_settings: ArxivSettings):
        """Test pdf_cache_dir creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            new_cache_path = Path(tmp_dir) / "new_cache"
            assert not new_cache_path.exists()
            
            settings = ArxivSettings(pdf_cache_dir=str(new_cache_path))
            client = ArxivClient(settings)
            
            _ = client.pdf_cache_dir
            assert new_cache_path.exists()


class TestGetPdfPath:
    """Test _get_pdf_path method."""

    def test_get_pdf_path_simple_id(self, arxiv_client: ArxivClient):
        """Test _get_pdf_path with simple arxiv ID."""
        arxiv_id = "2101.12345v1"
        path = arxiv_client._get_pdf_path(arxiv_id)
        assert path.name == "2101.12345v1.pdf"
        assert path.parent == arxiv_client.pdf_cache_dir

    def test_get_pdf_path_with_slash(self, arxiv_client: ArxivClient):
        """Test _get_pdf_path with arxiv ID containing slash."""
        arxiv_id = "astro-ph/0601001"
        path = arxiv_client._get_pdf_path(arxiv_id)
        assert path.name == "astro-ph_0601001.pdf"
        assert "_" in path.name  # slash replaced with underscore

    def test_get_pdf_path_consistency(self, arxiv_client: ArxivClient):
        """Test _get_pdf_path returns same path for same ID."""
        arxiv_id = "2101.12345v1"
        path1 = arxiv_client._get_pdf_path(arxiv_id)
        path2 = arxiv_client._get_pdf_path(arxiv_id)
        assert path1 == path2


class TestIsPdfCached:
    """Test _is_pdf_cached method."""

    def test_is_pdf_cached_returns_false_for_missing_file(self, arxiv_client: ArxivClient):
        """Test _is_pdf_cached returns False when PDF doesn't exist."""
        arxiv_id = "2101.12345v1"
        assert not arxiv_client._is_pdf_cached(arxiv_id)

    def test_is_pdf_cached_returns_true_for_existing_file(self, arxiv_client: ArxivClient):
        """Test _is_pdf_cached returns True when PDF exists."""
        arxiv_id = "2101.12345v1"
        pdf_path = arxiv_client._get_pdf_path(arxiv_id)
        pdf_path.touch()  # Create empty file
        
        assert arxiv_client._is_pdf_cached(arxiv_id)

    def test_is_pdf_cached_returns_false_for_directory(self, arxiv_client: ArxivClient):
        """Test _is_pdf_cached returns False for directory instead of file."""
        arxiv_id = "2101.12345v1"
        pdf_path = arxiv_client._get_pdf_path(arxiv_id)
        pdf_path.mkdir(parents=True, exist_ok=True)
        
        assert not arxiv_client._is_pdf_cached(arxiv_id)


class TestSearchPapers:
    """Test search_papers method."""

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_search_papers_success(self, mock_arxiv_client_class):
        """Test successful paper search."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance

        mock_author = Mock()
        mock_author.name = "John Doe"
        
        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = "2101.12345v1"
        mock_result.title = "Test Paper"
        mock_result.authors = [mock_author]
        mock_result.summary = "Test abstract"
        mock_result.categories = ["cs.AI", "cs.LG"]
        mock_result.published = datetime(2021, 1, 1)
        mock_result.pdf_url = "http://example.com/paper.pdf"

        mock_client_instance.results.return_value = [mock_result]

        # Create client and search
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            papers = client.search_papers("machine learning", max_results=1)

        # Assertions
        assert len(papers) == 1
        assert papers[0].arxiv_id == "2101.12345v1"
        assert papers[0].title == "Test Paper"
        assert papers[0].authors == ["John Doe"]
        assert papers[0].abstract == "Test abstract"
        assert papers[0].categories == ["cs.AI", "cs.LG"]

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_search_papers_empty_results(self, mock_arxiv_client_class):
        """Test search with no results."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance
        mock_client_instance.results.return_value = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            papers = client.search_papers("nonexistent", max_results=1)

        assert len(papers) == 0

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_search_papers_multiple_authors(self, mock_arxiv_client_class):
        """Test search with paper having multiple authors."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance

        authors = [Mock(name="Alice"), Mock(name="Bob"), Mock(name="Charlie")]
        for i, author in enumerate(authors):
            author.name = ["Alice", "Bob", "Charlie"][i]

        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = "2101.12345v1"
        mock_result.title = "Test Paper"
        mock_result.authors = authors
        mock_result.summary = "Test abstract"
        mock_result.categories = ["cs.AI"]
        mock_result.published = datetime(2021, 1, 1)
        mock_result.pdf_url = "http://example.com/paper.pdf"

        mock_client_instance.results.return_value = [mock_result]

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            papers = client.search_papers("machine learning")

        assert len(papers[0].authors) == 3
        assert papers[0].authors == ["Alice", "Bob", "Charlie"]

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_search_papers_http_error(self, mock_arxiv_client_class):
        """Test search handles HTTPError."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance
        mock_client_instance.results.side_effect = HTTPError(url="some_url", retry=0, status=500)

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            with pytest.raises(HTTPError):
                client.search_papers("query")


class TestGetById:
    """Test get_by_id method."""

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_get_by_id_success(self, mock_arxiv_client_class):
        """Test successful retrieval of paper by ID."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance

        mock_author = Mock()
        mock_author.name = "John Doe"

        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = "2101.12345v1"
        mock_result.title = "Test Paper"
        mock_result.authors = [mock_author]
        mock_result.summary = "Test abstract"
        mock_result.categories = ["cs.AI"]
        mock_result.published = datetime(2021, 1, 1)
        mock_result.pdf_url = "http://example.com/paper.pdf"

        mock_client_instance.results.return_value = [mock_result]

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            paper, result = client.get_by_id("2101.12345v1")

        assert paper is not None
        assert paper.arxiv_id == "2101.12345v1"
        assert result is not None

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_get_by_id_not_found(self, mock_arxiv_client_class):
        """Test get_by_id raises EntityNotFound when paper not found."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance
        mock_client_instance.results.side_effect = HTTPError(url="some_url", retry=0, status=404)

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            with pytest.raises(EntityNotFound):
                client.get_by_id("nonexistent")

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_get_by_id_returns_none_for_empty_results(self, mock_arxiv_client_class):
        """Test get_by_id returns (None, None) for empty results."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance
        mock_client_instance.results.return_value = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            paper, result = client.get_by_id("2101.12345v1")

        assert paper is None
        assert result is None


class TestDownloadPdf:
    """Test download_pdf method."""

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_download_pdf_success(self, mock_arxiv_client_class, arxiv_client: ArxivClient):
        """Test successful PDF download."""
        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = "2101.12345v1"
        
        # Create actual PDF file to simulate download
        pdf_path = arxiv_client._get_pdf_path("2101.12345v1")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_text("mock pdf content")
        
        mock_result.download_pdf.return_value = str(pdf_path)

        result_path = arxiv_client.download_pdf(mock_result)

        assert result_path == str(pdf_path)
        assert Path(result_path).exists()

    def test_download_pdf_uses_cache(self, arxiv_client: ArxivClient):
        """Test download_pdf uses cached PDF if available."""
        arxiv_id = "2101.12345v1"
        pdf_path = arxiv_client._get_pdf_path(arxiv_id)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_text("cached pdf")

        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = arxiv_id
        mock_result.download_pdf = Mock()

        result_path = arxiv_client.download_pdf(mock_result, force_download=False)

        assert result_path == str(pdf_path)
        mock_result.download_pdf.assert_not_called()

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_download_pdf_force_download(self, mock_arxiv_client_class, arxiv_client: ArxivClient):
        """Test download_pdf with force_download=True bypasses cache."""
        arxiv_id = "2101.12345v1"
        pdf_path = arxiv_client._get_pdf_path(arxiv_id)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_text("old cached pdf")

        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = arxiv_id
        pdf_path.write_text("new pdf content")
        mock_result.download_pdf.return_value = str(pdf_path)

        result_path = arxiv_client.download_pdf(mock_result, force_download=True)

        assert result_path == str(pdf_path)
        mock_result.download_pdf.assert_called_once()

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_download_pdf_with_custom_filename(self, mock_arxiv_client_class, arxiv_client: ArxivClient):
        """Test download_pdf with custom filename."""
        custom_filename = "custom_name.pdf"
        pdf_path = arxiv_client.pdf_cache_dir / custom_filename
        pdf_path.write_text("pdf content")

        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = "2101.12345v1"
        mock_result.download_pdf.return_value = str(pdf_path)

        result_path = arxiv_client.download_pdf(mock_result, filename=custom_filename)

        assert result_path == str(pdf_path)
        mock_result.download_pdf.assert_called_once_with(
            dirpath=str(arxiv_client.pdf_cache_dir),
            filename=custom_filename
        )

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_download_pdf_file_not_found_after_download(self, mock_arxiv_client_class, arxiv_client: ArxivClient):
        """Test download_pdf raises FileNotFoundError if file doesn't exist after download."""
        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = "2101.12345v1"
        mock_result.download_pdf.return_value = str(arxiv_client.pdf_cache_dir / "nonexistent.pdf")

        with pytest.raises(FileNotFoundError):
            arxiv_client.download_pdf(mock_result)


class TestGetByIdAndDownload:
    """Test get_by_id_and_download method."""

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_get_by_id_and_download_success(self, mock_arxiv_client_class):
        """Test successful retrieval and download."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance

        mock_author = Mock()
        mock_author.name = "John Doe"

        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = "2101.12345v1"
        mock_result.title = "Test Paper"
        mock_result.authors = [mock_author]
        mock_result.summary = "Test abstract"
        mock_result.categories = ["cs.AI"]
        mock_result.published = datetime(2021, 1, 1)
        mock_result.pdf_url = "http://example.com/paper.pdf"

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            # Mock the results
            mock_client_instance.results.return_value = [mock_result]
            
            # Create the PDF file to satisfy the check
            pdf_path = client._get_pdf_path("2101.12345v1")
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            pdf_path.write_text("test pdf")
            mock_result.download_pdf.return_value = str(pdf_path)

            pdf_path_result, paper = client.get_by_id_and_download("2101.12345v1", download_pdf=True)

        assert pdf_path_result is not None
        assert paper is not None
        assert paper.arxiv_id == "2101.12345v1"

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_get_by_id_and_download_without_pdf(self, mock_arxiv_client_class):
        """Test get_by_id_and_download without downloading PDF."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance

        mock_author = Mock()
        mock_author.name = "John Doe"

        mock_result = Mock(spec=arxiv.Result)
        mock_result.entry_id = "2101.12345v1"
        mock_result.title = "Test Paper"
        mock_result.authors = [mock_author]
        mock_result.summary = "Test abstract"
        mock_result.categories = ["cs.AI"]
        mock_result.published = datetime(2021, 1, 1)
        mock_result.pdf_url = "http://example.com/paper.pdf"

        mock_client_instance.results.return_value = [mock_result]

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            pdf_path_result, paper = client.get_by_id_and_download(
                "2101.12345v1",
                download_pdf=False
            )

        assert pdf_path_result is None
        assert paper is not None

    @patch('arxiv_lib.arxiv.client.arxiv.Client')
    def test_get_by_id_and_download_not_found(self, mock_arxiv_client_class):
        """Test get_by_id_and_download returns None when paper not found."""
        mock_client_instance = MagicMock()
        mock_arxiv_client_class.return_value = mock_client_instance
        mock_client_instance.results.side_effect = HTTPError(url="some_url", retry=0, status=404)

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = ArxivSettings(pdf_cache_dir=tmp_dir)
            client = ArxivClient(settings)
            client.client = mock_client_instance

            with pytest.raises(EntityNotFound):
                client.get_by_id_and_download("nonexistent")


class TestClearCache:
    """Test clear_cache method."""

    def test_clear_cache_removes_all_pdfs(self, arxiv_client: ArxivClient):
        """Test clear_cache removes all cached PDFs."""
        # Create some test PDF files
        pdf1 = arxiv_client._get_pdf_path("2101.12345v1")
        pdf2 = arxiv_client._get_pdf_path("2102.54321v1")
        pdf1.write_text("pdf1")
        pdf2.write_text("pdf2")

        assert pdf1.exists()
        assert pdf2.exists()

        arxiv_client.clear_cache()

        assert not pdf1.exists()
        assert not pdf2.exists()
        assert arxiv_client.pdf_cache_dir.exists()

    def test_clear_cache_creates_empty_directory(self, arxiv_client: ArxivClient):
        """Test clear_cache recreates empty cache directory."""
        pdf = arxiv_client._get_pdf_path("2101.12345v1")
        pdf.write_text("pdf")

        arxiv_client.clear_cache()

        assert arxiv_client.pdf_cache_dir.exists()
        assert len(list(arxiv_client.pdf_cache_dir.glob("*.pdf"))) == 0


class TestCleanupOldPdfs:
    """Test cleanup_old_pdfs method."""

    def test_cleanup_old_pdfs_removes_old_files(self, arxiv_client: ArxivClient):
        """Test cleanup_old_pdfs removes files older than specified days."""
        # Create old PDF
        old_pdf = arxiv_client._get_pdf_path("2101.12345v1")
        old_pdf.write_text("old pdf")
        
        # Set modification time to 2 days ago
        old_time = datetime.now() - timedelta(days=2)
        old_pdf.stat()
        import os
        os.utime(old_pdf, (old_time.timestamp(), old_time.timestamp()))

        # Create new PDF
        new_pdf = arxiv_client._get_pdf_path("2102.54321v1")
        new_pdf.write_text("new pdf")

        deleted_count = arxiv_client.cleanup_old_pdfs(days=1)

        assert deleted_count == 1
        assert not old_pdf.exists()
        assert new_pdf.exists()

    def test_cleanup_old_pdfs_keeps_recent_files(self, arxiv_client: ArxivClient):
        """Test cleanup_old_pdfs keeps files newer than specified days."""
        # Create recent PDF
        recent_pdf = arxiv_client._get_pdf_path("2101.12345v1")
        recent_pdf.write_text("recent pdf")

        deleted_count = arxiv_client.cleanup_old_pdfs(days=1)

        assert deleted_count == 0
        assert recent_pdf.exists()

    def test_cleanup_old_pdfs_negative_days_raises_error(self, arxiv_client: ArxivClient):
        """Test cleanup_old_pdfs raises ValueError for negative days."""
        with pytest.raises(ValueError, match="days cannot be negative"):
            arxiv_client.cleanup_old_pdfs(days=-1)

    def test_cleanup_old_pdfs_returns_count(self, arxiv_client: ArxivClient):
        """Test cleanup_old_pdfs returns correct count of deleted files."""
        # Create multiple old PDFs
        for i in range(3):
            pdf = arxiv_client._get_pdf_path(f"210{i}.12345v1")
            pdf.write_text(f"old pdf {i}")
            old_time = datetime.now() - timedelta(days=2)
            import os
            os.utime(pdf, (old_time.timestamp(), old_time.timestamp()))

        deleted_count = arxiv_client.cleanup_old_pdfs(days=1)

        assert deleted_count == 3


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager_entry_exit(self, arxiv_settings: ArxivSettings):
        """Test context manager __enter__ and __exit__."""
        with ArxivClient(arxiv_settings) as client:
            assert client is not None
            assert client._settings == arxiv_settings

    def test_context_manager_with_exception(self, arxiv_settings: ArxivSettings):
        """Test context manager handles exceptions."""
        try:
            with ArxivClient(arxiv_settings) as client:
                raise RuntimeError("Test error")
        except RuntimeError:
            pass  # Expected
