import logging
from typing import Dict, List
from uuid import uuid4

from arxiv_lib.vector_db.qdrant import QdrantDB
from services.embeddings.inference import FastembedEmbeddingsClient

from .text_chunker import TextChunker

logger = logging.getLogger(__name__)


class HybridIndexingService:
    """Service for indexing papers with chunking and embeddings for hybrid search.

    Orchestrates the process of:
    1. Chunking papers into overlapping segments
    2. Generating embeddings for each chunk
    3. Indexing chunks with embeddings into OpenSearch
    """

    def __init__(
        self,
        chunker: TextChunker,
        embeddings_client: FastembedEmbeddingsClient,
        vector_db_client: QdrantDB,
        embedding_batch_size: int = 10,
    ):
        """Initialize hybrid indexing service.

        :param chunker: Text chunking service
        :param embeddings_client: Embeddings generation client
        :param vector_db_client: Vector database client
        :param embedding_batch_size: Batch size for processing embeddings (default: 5)
        """
        self.chunker = chunker
        self.embeddings_client = embeddings_client
        self.vector_db_client = vector_db_client
        self.embedding_batch_size = embedding_batch_size
        logger.info("Hybrid indexing service initialized")

    def index_paper(self, paper_data: Dict, collection_name: str) -> Dict[str, int]:
        """Index a single paper with chunking and embeddings.

        :param paper_data: Paper data from database
        :param collection_name: Name of the collection in the vector database
        :returns: Dictionary with indexing statistics
        """
        arxiv_id = paper_data.get("arxiv_id")
        paper_id = str(paper_data.get("id", ""))

        if not arxiv_id:
            logger.error("Paper missing arxiv_id")
            return {
                "chunks_created": 0,
                "chunks_indexed": 0,
                "embeddings_generated": 0,
                "errors": 1,
            }

        # Ensure collection exists before adding documents
        try:
            if collection_name not in self.vector_db_client.list_collections():
                self.vector_db_client.create_collection(collection_name, hybrid=True)
        except Exception as e:
            logger.warning(f"Could not create collection: {e}")

        if self.vector_db_client.content_exists(collection_name, {"arxiv_id": arxiv_id}) is True:
            logger.error("Paper already exists")
            return {
                "chunks_created": 0,
                "chunks_indexed": 0,
                "embeddings_generated": 0,
                "errors": 0,
            }

        try:
            # Step 1: Chunk the paper using hybrid section-based approach
            chunks = self.chunker.chunk_paper(
                title=paper_data.get("title", ""),
                abstract=paper_data.get("abstract", ""),
                full_text=paper_data.get("raw_text", paper_data.get("full_text", "")),
                arxiv_id=arxiv_id,
                paper_id=paper_id,
                sections=paper_data.get("sections"),
            )

            if not chunks:
                logger.warning(f"No chunks created for paper {arxiv_id}")
                return {
                    "chunks_created": 0,
                    "chunks_indexed": 0,
                    "embeddings_generated": 0,
                    "errors": 0,
                }

            logger.info(f"Created {len(chunks)} chunks for paper {arxiv_id}")

            # Step 2: Generate embeddings for chunks in batches
            chunk_texts = [chunk.text for chunk in chunks]
            dense_embeddings = []
            sparse_embeddings = []

            for i in range(0, len(chunk_texts), self.embedding_batch_size):
                batch_texts = chunk_texts[i : i + self.embedding_batch_size]
                logger.info(
                    f"Processing embedding batch {i // self.embedding_batch_size + 1}, "
                    f"texts: {len(batch_texts)}"
                )

                batch_dense = self.embeddings_client.generate_dense_embeddings(texts=batch_texts)
                batch_sparse = self.embeddings_client.generate_sparse_embeddings(texts=batch_texts)

                dense_embeddings.extend(batch_dense)
                sparse_embeddings.extend(batch_sparse)

            if len(dense_embeddings) != len(chunks):
                logger.error(
                    f"Dense embedding count mismatch: {len(dense_embeddings)} != {len(chunks)}"
                )
                return {
                    "chunks_created": len(chunks),
                    "chunks_indexed": 0,
                    "embeddings_generated": len(dense_embeddings),
                    "errors": 1,
                }

            if len(sparse_embeddings) != len(chunks):
                logger.error(
                    f"Sparse embedding count mismatch: {len(sparse_embeddings)} != {len(chunks)}"
                )
                return {
                    "chunks_created": len(chunks),
                    "chunks_indexed": 0,
                    "embeddings_generated": len(dense_embeddings),
                    "errors": 1,
                }

            # Step 3: Prepare chunks with embeddings for indexing
            chunks_with_embeddings = []

            for chunk, dense_embedding, sparse_embedding in zip(
                chunks, dense_embeddings, sparse_embeddings
            ):
                # Prepare chunk data for OpenSearch
                chunk_metadata = {
                    "arxiv_id": chunk.arxiv_id,
                    "paper_id": chunk.paper_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "chunk_text": chunk.text,
                    "chunk_word_count": chunk.metadata.word_count,
                    "start_char": chunk.metadata.start_char,
                    "end_char": chunk.metadata.end_char,
                    "section_title": chunk.metadata.section_title,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "sparse_model": "prithivida/Splade_PP_en_v1",
                    # Denormalized paper metadata for efficient search
                    "title": paper_data.get("title", ""),
                    "authors": ", ".join(paper_data.get("authors", []))
                    if isinstance(paper_data.get("authors"), list)
                    else paper_data.get("authors", ""),
                    "abstract": paper_data.get("abstract", ""),
                    "categories": paper_data.get("categories", []),
                    "published_date": paper_data.get("published_date"),
                }

                chunks_with_embeddings.append(
                    {
                        "id": str(uuid4()),
                        "metadata": chunk_metadata,
                        "dense_embedding": dense_embedding,
                        "sparse_embedding": sparse_embedding,
                    }
                )

            # Step 4: Index chunks into vector database in batches
            for j in range(0, len(chunks_with_embeddings), self.embedding_batch_size):
                batch = chunks_with_embeddings[j : j + self.embedding_batch_size]
                logger.info(
                    f"Indexing batch {j // self.embedding_batch_size + 1} with {len(batch)} "
                    f"chunks to collection {collection_name}"
                )
                self.vector_db_client.add_batch_docs(collection_name, batch, hybrid=True)

            logger.info(f"Indexed paper {arxiv_id}: success")

            return {
                "chunks_created": len(chunks),
                "chunks_indexed": len(chunks),
                "embeddings_generated": len(dense_embeddings),
                "sparse_embeddings_generated": len(sparse_embeddings),
                "errors": 0,
            }

        except Exception as e:
            logger.error(f"Error indexing paper {arxiv_id}: {e}")
            return {
                "chunks_created": 0,
                "chunks_indexed": 0,
                "embeddings_generated": 0,
                "errors": 1,
            }

    def index_papers_batch(
        self, papers: List[Dict], collection_name: str, replace_existing: bool = False
    ) -> Dict[str, int]:
        """Index multiple papers in batch.

        :param papers: List of paper data
        :param replace_existing: If True, delete existing chunks before indexing
        :returns: Aggregated statistics
        """
        total_stats = {
            "papers_processed": 0,
            "total_chunks_created": 0,
            "total_chunks_indexed": 0,
            "total_embeddings_generated": 0,
            "total_errors": 0,
        }

        for paper in papers:
            arxiv_id = paper.get("arxiv_id")

            # Optionally delete existing chunks
            if (
                replace_existing
                and arxiv_id
                and collection_name in self.vector_db_client.list_collections()
            ):
                self.vector_db_client.delete_doc(collection_name, "arxiv_id", arxiv_id)
                logger.info(f"Deleted chunks for paper {arxiv_id}")

            # Index the paper
            stats = self.index_paper(paper, collection_name=collection_name)

            # Update totals
            total_stats["papers_processed"] += 1
            total_stats["total_chunks_created"] += stats["chunks_created"]
            total_stats["total_chunks_indexed"] += stats["chunks_indexed"]
            total_stats["total_embeddings_generated"] += stats["embeddings_generated"]
            total_stats["total_errors"] += stats["errors"]

        logger.info(
            f"Batch indexing complete: {total_stats['papers_processed']} papers, "
            f"{total_stats['total_chunks_indexed']} chunks indexed"
        )

        return total_stats
