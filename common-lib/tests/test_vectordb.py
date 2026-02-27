from unittest.mock import MagicMock, patch

import pytest
from arxiv_lib.vector_db.qdrant import QdrantDB
from qdrant_client.http.exceptions import UnexpectedResponse

# ---------------------------------------------------------
# Fixtures
# ---------------------------------------------------------


@pytest.fixture
def mock_client():
    with patch("arxiv_lib.vector_db.qdrant.QdrantClient") as mock:
        yield mock


@pytest.fixture
def db(mock_client):
    return QdrantDB(host="localhost", port=6333)


# ---------------------------------------------------------
# Utility Tests
# ---------------------------------------------------------


def test_string_to_positive_int_is_deterministic():
    val1 = QdrantDB._string_to_positive_int("doc1")
    val2 = QdrantDB._string_to_positive_int("doc1")
    assert val1 == val2
    assert val1 >= 0


# ---------------------------------------------------------
# Collection Methods
# ---------------------------------------------------------


def test_create_collection_basic(db):
    db.client.create_collection = MagicMock()

    db.create_collection("test_collection")

    db.client.create_collection.assert_called_once()


def test_create_collection_hybrid(db):
    db.client.create_collection = MagicMock()

    db.create_collection("hybrid_collection", hybrid=True)

    db.client.create_collection.assert_called_once()
    args = db.client.create_collection.call_args.kwargs
    assert args["hnsw_config"] is not None
    assert args["quantization_config"] is not None
    assert args["sparse_vectors_config"] is not None


def test_create_collection_unexpected_response(db):
    db.client.create_collection = MagicMock(
        side_effect=UnexpectedResponse("error", "error", "error", "error")
    )

    with pytest.raises(UnexpectedResponse):
        db.create_collection("fail_collection")


def test_delete_collection(db):
    db.client.delete_collection = MagicMock()

    db.delete_collection("col")

    db.client.delete_collection.assert_called_once_with(collection_name="col")


def test_list_collections(db):
    mock_collections = MagicMock()
    mock_collections.collections = [
        MagicMock(name="col1"),
        MagicMock(name="col2"),
    ]
    mock_collections.collections[0].name = "col1"
    mock_collections.collections[1].name = "col2"

    db.client.get_collections = MagicMock(return_value=mock_collections)

    result = db.list_collections()

    assert result == ["col1", "col2"]


# ---------------------------------------------------------
# Document Insert
# ---------------------------------------------------------


def test_add_doc(db):
    db.client.upsert = MagicMock()

    db.add_doc("col", "doc1", [0.1, 0.2], {"a": 1})

    db.client.upsert.assert_called_once()


def test_add_doc_unexpected_response(db):
    db.client.upsert = MagicMock(side_effect=UnexpectedResponse("fail", "fail", "fail", "fail"))

    with pytest.raises(UnexpectedResponse):
        db.add_doc("col", "doc1", [0.1])


# ---------------------------------------------------------
# Batch Insert
# ---------------------------------------------------------


def test_add_batch_docs_basic(db):
    db.client.upsert = MagicMock()

    docs = [
        {"id": "doc1", "dense_embedding": [0.1, 0.2]},
        {"id": "doc2", "dense_embedding": [0.3, 0.4]},
    ]

    db.add_batch_docs("col", docs)

    db.client.upsert.assert_called_once()


def test_add_batch_docs_hybrid(db):
    db.client.upsert = MagicMock()

    docs = [
        {
            "id": "doc1",
            "dense_embedding": [0.1],
            "sparse_embedding": {"indices": [1], "values": [0.5]},
        }
    ]

    db.add_batch_docs("col", docs, hybrid=True)

    db.client.upsert.assert_called_once()


def test_add_batch_docs_invalid_id(db):
    with pytest.raises(RuntimeError):
        db.add_batch_docs("col", [{"dense_embedding": [0.1]}])


def test_add_batch_docs_invalid_dense(db):
    with pytest.raises(RuntimeError):
        db.add_batch_docs("col", [{"id": "doc1"}])


def test_add_batch_docs_invalid_sparse_hybrid(db):
    with pytest.raises(RuntimeError):
        db.add_batch_docs(
            "col",
            [{"id": "doc1", "dense_embedding": [0.1]}],
            hybrid=True,
        )


# ---------------------------------------------------------
# Delete Doc
# ---------------------------------------------------------


def test_delete_doc(db):
    db.client.delete = MagicMock()

    db.delete_doc("col", "doc_name", "doc_id")

    db.client.delete.assert_called_once()


# ---------------------------------------------------------
# Search
# ---------------------------------------------------------


def test_search_docs_basic(db):
    mock_result = MagicMock()
    mock_result.points = [
        MagicMock(id=1, score=0.9, payload={"a": 1}),
        MagicMock(id=2, score=0.8, payload={"b": 2}),
    ]

    db.client.query_points = MagicMock(return_value=mock_result)

    results = db.search_docs(
        collection_name="col",
        query_vector={"embeddings": [[0.1, 0.2]]},
        limit=2,
    )

    assert len(results) == 2
    assert results[0]["score"] == 0.9


def test_search_docs_invalid_query_vector(db):
    with pytest.raises(RuntimeError):
        db.search_docs("col", query_vector={}, limit=1)


def test_search_docs_hybrid(db):
    with patch.object(db, "_hybrid_search") as hybrid_mock:
        hybrid_mock.return_value = MagicMock(points=[MagicMock(id=1, score=0.9, payload={})])

        results = db.search_docs(
            collection_name="col",
            query_vector={
                "embeddings": [[0.1]],
                "sparse_embeddings": [{"indices": [1], "values": [0.5]}],
            },
            hybrid=True,
        )

        assert len(results) == 1
        hybrid_mock.assert_called_once()


# ---------------------------------------------------------
# Hybrid Search Internal
# ---------------------------------------------------------


def test_hybrid_search_success(db):
    db.client.query_points = MagicMock(return_value=MagicMock())

    result = db._hybrid_search(
        collection_name="col",
        sparse_vector={"indices": [1], "values": [0.5]},
        dense_vector=[0.1],
        limit=1,
    )

    db.client.query_points.assert_called_once()
    assert result is not None


# ---------------------------------------------------------
# Content Exists
# ---------------------------------------------------------


def test_content_exists_true(db):
    db.client.count = MagicMock(return_value=MagicMock(count=1))

    exists = db.content_exists("col", {"key": "value"})

    assert exists is True


def test_content_exists_false(db):
    db.client.count = MagicMock(return_value=MagicMock(count=0))

    exists = db.content_exists("col", {"key": "value"})

    assert exists is False
