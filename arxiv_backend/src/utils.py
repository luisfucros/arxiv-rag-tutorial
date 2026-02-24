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
