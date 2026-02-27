import uuid
from datetime import datetime, timedelta, timezone

import pytest
from arxiv_lib.db.databases.postgresql import Base
from arxiv_lib.repositories.paper import PaperRepository
from arxiv_lib.schemas import PaperCreate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------
# Database Fixture
# ---------------------------------------------------------


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def repository(db_session):
    return PaperRepository(db_session)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def create_paper_schema(**overrides) -> PaperCreate:
    """
    Creates a valid PaperCreate schema with defaults.
    """
    data = {
        "arxiv_id": str(uuid.uuid4()),
        "title": "Test Paper",
        "authors": ["Author One", "Author Two"],
        "abstract": "Test abstract",
        "categories": ["cs.AI"],
        "published_date": datetime.now(timezone.utc),
        "pdf_url": "http://arxiv.org/pdf/test.pdf",
        "raw_text": None,
        "sections": None,
        "references": None,
        "parser_used": None,
        "parser_metadata": None,
        "pdf_processed": False,
        "pdf_processing_date": None,
    }
    data.update(overrides)
    return PaperCreate(**data)


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------


def test_create(repository):
    paper_data = create_paper_schema()
    paper = repository.create(paper_data)

    assert paper.id is not None
    assert paper.arxiv_id == paper_data.arxiv_id
    assert repository.get_count() == 1


def test_get_by_arxiv_id(repository):
    paper_data = create_paper_schema()
    repository.create(paper_data)

    result = repository.get_by_arxiv_id(paper_data.arxiv_id)

    assert result is not None
    assert result.arxiv_id == paper_data.arxiv_id


def test_get_by_id(repository):
    paper_data = create_paper_schema()
    created = repository.create(paper_data)

    result = repository.get_by_id(created.id)

    assert result is not None
    assert result.id == created.id


def test_get_all_ordered_by_published_date(repository):
    older = repository.create(
        create_paper_schema(published_date=datetime.now(timezone.utc) - timedelta(days=2))
    )

    newer = repository.create(create_paper_schema(published_date=datetime.now(timezone.utc)))

    papers = repository.get_all()

    assert len(papers) == 2
    assert papers[0].id == newer.id
    assert papers[1].id == older.id


def test_get_count(repository):
    assert repository.get_count() == 0
    repository.create(create_paper_schema())
    repository.create(create_paper_schema())
    assert repository.get_count() == 2


# def test_get_processed_papers(repository):
#     repository.create(create_paper_schema(pdf_processed=True))
#     repository.create(create_paper_schema(pdf_processed=False))

#     processed = repository.get_processed_papers()

#     assert len(processed) == 1
#     assert processed[0].pdf_processed is True


# def test_get_unprocessed_papers(repository):
#     repository.create(create_paper_schema(pdf_processed=True))
#     repository.create(create_paper_schema(pdf_processed=False))

#     unprocessed = repository.get_unprocessed_papers()

#     assert len(unprocessed) == 1
#     assert unprocessed[0].pdf_processed is False


# def test_get_papers_with_raw_text(repository):
#     repository.create(create_paper_schema(raw_text="Full PDF text"))
#     repository.create(create_paper_schema(raw_text=None))

#     papers = repository.get_papers_with_raw_text()

#     assert len(papers) == 1
#     assert papers[0].raw_text == "Full PDF text"


# def test_get_processing_stats(repository):
#     """
#     total = 3
#     processed = 2
#     with text = 1
#     """
#     repository.create(create_paper_schema(pdf_processed=True, raw_text="text"))
#     repository.create(create_paper_schema(pdf_processed=True))
#     repository.create(create_paper_schema(pdf_processed=False))

#     stats = repository.get_processing_stats()

#     assert stats["total_papers"] == 3
#     assert stats["processed_papers"] == 2
#     assert stats["papers_with_text"] == 1

#     assert stats["processing_rate"] == pytest.approx(66.66, rel=1e-2)
#     assert stats["text_extraction_rate"] == pytest.approx(50.0)


def test_update(repository):
    paper = repository.create(create_paper_schema())
    paper.title = "Updated Title"

    updated = repository.update(paper)

    assert updated.title == "Updated Title"
    assert repository.get_by_id(paper.id).title == "Updated Title"


def test_upsert_create(repository):
    paper_data = create_paper_schema()

    result = repository.upsert(paper_data)

    assert result is not None
    assert repository.get_count() == 1


def test_upsert_update(repository):
    repository.create(create_paper_schema(arxiv_id="1234.5678"))

    updated_data = create_paper_schema(
        arxiv_id="1234.5678",
        title="Updated Title",
        abstract="Updated abstract",
    )

    result = repository.upsert(updated_data)

    assert repository.get_count() == 1
    assert result.title == "Updated Title"
    assert result.abstract == "Updated abstract"
