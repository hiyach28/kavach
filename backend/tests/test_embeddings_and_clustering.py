"""Unit tests for embeddings (F23) and clustering (F24) — pure unit, no DB."""
import pytest

from app.services.embeddings import embed, _mock_embed
from app.services.clustering import _build_graph, _louvain_partition
import uuid


# ── Embedding tests ──────────────────────────────────────────────────────────

def test_mock_embed_returns_correct_dim() -> None:
    vec = _mock_embed("hello world")
    assert len(vec) == 768


def test_mock_embed_is_deterministic() -> None:
    v1 = _mock_embed("customs officer arrested you send 50000")
    v2 = _mock_embed("customs officer arrested you send 50000")
    assert v1 == v2


def test_mock_embed_different_texts_differ() -> None:
    v1 = _mock_embed("invest in crypto now 200% returns")
    v2 = _mock_embed("customs officer arrested send money")
    # Should not be identical
    assert v1 != v2


def test_mock_embed_values_in_range() -> None:
    vec = _mock_embed("test text for range checking")
    assert all(-1.0 <= f <= 1.0 for f in vec)


def test_embed_in_mock_mode(monkeypatch) -> None:
    monkeypatch.setattr("app.services.embeddings.settings.LLM_MODE", "mock")
    monkeypatch.setattr("app.services.embeddings.settings.EMBED_MODE", "")
    vec = embed("any text")
    assert len(vec) == 768


# ── Clustering unit tests ────────────────────────────────────────────────────

def test_build_graph_two_cases_share_entity() -> None:
    c1, c2 = uuid.uuid4(), uuid.uuid4()
    e1 = uuid.uuid4()
    G = _build_graph(
        case_ids={c1, c2},
        entity_ids={e1},
        case_entity_edges=[(c1, e1), (c2, e1)],
        semantic_edges=[],
    )
    assert G.has_edge(str(c1), str(c2))


def test_build_graph_no_shared_entities_no_edge() -> None:
    c1, c2 = uuid.uuid4(), uuid.uuid4()
    e1, e2 = uuid.uuid4(), uuid.uuid4()
    G = _build_graph(
        case_ids={c1, c2},
        entity_ids={e1, e2},
        case_entity_edges=[(c1, e1), (c2, e2)],
        semantic_edges=[],
    )
    assert not G.has_edge(str(c1), str(c2))


def test_build_graph_semantic_edge_connects_cases() -> None:
    c1, c2 = uuid.uuid4(), uuid.uuid4()
    G = _build_graph(
        case_ids={c1, c2},
        entity_ids=set(),
        case_entity_edges=[],
        semantic_edges=[(c1, c2, 0.9)],
    )
    assert G.has_edge(str(c1), str(c2))


def test_louvain_groups_connected_cases() -> None:
    """Three cases sharing entities should land in the same community."""
    import networkx as nx
    c1, c2, c3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    e1 = uuid.uuid4()
    G = _build_graph(
        case_ids={c1, c2, c3},
        entity_ids={e1},
        case_entity_edges=[(c1, e1), (c2, e1), (c3, e1)],
        semantic_edges=[],
    )
    partition = _louvain_partition(G)
    # All three should be in the same community
    assert partition[str(c1)] == partition[str(c2)] == partition[str(c3)]


def test_louvain_isolates_unconnected_cases() -> None:
    """Two distinct clusters → different communities."""
    c1, c2, c3, c4 = (uuid.uuid4() for _ in range(4))
    e1, e2 = uuid.uuid4(), uuid.uuid4()
    G = _build_graph(
        case_ids={c1, c2, c3, c4},
        entity_ids={e1, e2},
        case_entity_edges=[(c1, e1), (c2, e1), (c3, e2), (c4, e2)],
        semantic_edges=[],
    )
    partition = _louvain_partition(G)
    # Cluster A
    assert partition[str(c1)] == partition[str(c2)]
    # Cluster B
    assert partition[str(c3)] == partition[str(c4)]
    # Different clusters
    assert partition[str(c1)] != partition[str(c3)]
