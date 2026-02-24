from arxiv_lib.arxiv.client import ArxivClient
from arxiv_lib.db.factory import make_database
from arxiv_lib.vector_db.qdrant import QdrantDB
from config import settings
from services.embeddings.inference import FastembedEmbeddingsClient
from services.indexing.hybrid_indexer import HybridIndexingService
from services.indexing.text_chunker import TextChunker
from services.metadata_fetcher import MetadataFetcher
from services.pdf_parser.parser import PDFParserService


def get_services():

    database = make_database()

    arxiv_client = ArxivClient(settings=settings.arxiv)
    pdf_parser = PDFParserService(
        max_pages=settings.pdf_parser.max_pages,
        max_file_size_mb=settings.pdf_parser.max_file_size_mb,
        do_ocr=settings.pdf_parser.do_ocr,
        do_table_structure=settings.pdf_parser.do_table_structure,
    )

    fetcher = MetadataFetcher(
        arxiv_client=arxiv_client,
        pdf_parser=pdf_parser,
        settings=settings,
    )

    chunker = TextChunker(
        chunk_size=settings.chunking.chunk_size,
        overlap_size=settings.chunking.overlap_size,
        min_chunk_size=settings.chunking.min_chunk_size,
    )
    vector_db_client = QdrantDB(host=settings.vectordb_host, port=settings.vectordb_port)
    embeddings = FastembedEmbeddingsClient()

    hybrid_indexer = HybridIndexingService(chunker, embeddings, vector_db_client)

    return fetcher, database, hybrid_indexer
