from arxiv_lib.db_models.models import Paper


def paper_to_dict(paper: Paper) -> dict:
    return {
        "id": str(paper.id),
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "published_date": paper.published_date.isoformat() if paper.published_date else None,
        "pdf_processed": paper.pdf_processed,
        "pdf_processing_date": (
            paper.pdf_processing_date.isoformat() if paper.pdf_processing_date else None
        ),
    }


def paper_title_match_dict(paper: Paper, abstract_preview_chars: int = 400) -> dict:
    """Compact metadata for title search results so users can confirm the right paper."""
    abstract = paper.abstract or ""
    if len(abstract) > abstract_preview_chars:
        abstract_preview = abstract[:abstract_preview_chars].rstrip() + "…"
    else:
        abstract_preview = abstract
    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "authors": paper.authors,
        "published_date": paper.published_date.isoformat() if paper.published_date else None,
        "categories": paper.categories,
        "abstract_preview": abstract_preview,
        "pdf_url": paper.pdf_url,
        "pdf_processed": paper.pdf_processed,
    }
