"""Incremental campaign clustering (F24).

Algorithm:
  1. Given a set of entity_ids newly linked to a case, fetch the connected
     component in the case-entity graph (bounded to 2,000 nodes).
  2. Build a NetworkX bipartite graph of case nodes + entity nodes.
  3. Project onto case nodes (cases sharing ≥1 entity are co-incident).
  4. Supplement with semantic edges (SemanticLink, score ≥ SEMANTIC_THRESHOLD).
  5. Run Louvain community detection.
  6. Reconcile campaign IDs using stable-ID rule: existing campaign whose
     members have the largest overlap with a new community keeps its ID.
  7. Persist campaign assignments back to the DB.

Deferred path: if the component has >MAX_COMPONENT_NODES, the job is
deferred (caller marks case as `clustered` with campaign_id=None and
schedules a nightly full-recluster).
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict

import networkx as nx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import Campaign, Case, CaseEntityLink, SemanticLink

logger = logging.getLogger("kavach.cluster")

MAX_COMPONENT_NODES = 2_000
SEMANTIC_THRESHOLD = 0.75


# ── Graph construction ───────────────────────────────────────────────────────


async def _fetch_component(
    seed_case_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[set[uuid.UUID], set[uuid.UUID]]:
    """
    BFS from seed_case_id through case-entity edges.
    Returns (case_ids, entity_ids) in the component (bounded).
    """
    visited_cases: set[uuid.UUID] = set()
    visited_entities: set[uuid.UUID] = set()
    queue: list[uuid.UUID] = [seed_case_id]

    while queue and (len(visited_cases) + len(visited_entities)) < MAX_COMPONENT_NODES:
        case_id = queue.pop(0)
        if case_id in visited_cases:
            continue
        visited_cases.add(case_id)

        # Entities for this case
        links = (
            (
                await db.execute(
                    select(CaseEntityLink.entity_id).where(CaseEntityLink.case_id == case_id)
                )
            )
            .scalars()
            .all()
        )

        for ent_id in links:
            if ent_id in visited_entities:
                continue
            visited_entities.add(ent_id)
            # Other cases sharing this entity
            peer_cases = (
                (
                    await db.execute(
                        select(CaseEntityLink.case_id).where(CaseEntityLink.entity_id == ent_id)
                    )
                )
                .scalars()
                .all()
            )
            queue.extend(c for c in peer_cases if c not in visited_cases)

    return visited_cases, visited_entities


def _build_graph(
    case_ids: set[uuid.UUID],
    entity_ids: set[uuid.UUID],
    case_entity_edges: list[tuple[uuid.UUID, uuid.UUID]],
    semantic_edges: list[tuple[uuid.UUID, uuid.UUID, float]],
) -> nx.Graph:
    """Build case-projection graph.

    Two cases are connected if they share an entity or are semantically similar.
    """
    G = nx.Graph()
    G.add_nodes_from(str(c) for c in case_ids)

    # Build entity → cases mapping
    ent_to_cases: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for case_id, ent_id in case_entity_edges:
        ent_to_cases[ent_id].append(case_id)

    # Infrastructure edges
    for _, cases in ent_to_cases.items():
        for i, a in enumerate(cases):
            for b in cases[i + 1 :]:
                if str(a) in G and str(b) in G:
                    G.add_edge(str(a), str(b), weight=1.0, edge_type="infrastructure")

    # Semantic edges
    for a_id, b_id, score in semantic_edges:
        if str(a_id) in G and str(b_id) in G:
            G.add_edge(str(a_id), str(b_id), weight=score, edge_type="semantic")

    return G


def _louvain_partition(G: nx.Graph) -> dict[str, int]:
    """Run Louvain community detection. Returns {node_str: community_id}."""
    try:
        import community as community_louvain  # type: ignore[import]

        return community_louvain.best_partition(G, weight="weight", random_state=42)
    except ImportError:
        # Fallback to networkx greedy modularity
        from networkx.algorithms.community import greedy_modularity_communities

        communities = greedy_modularity_communities(G, weight="weight")
        partition: dict[str, int] = {}
        for comm_id, comm in enumerate(communities):
            for node in comm:
                partition[node] = comm_id
        return partition


# ── Stable-ID reconciliation ─────────────────────────────────────────────────


async def _reconcile_campaigns(
    partition: dict[str, int],
    db: AsyncSession,
) -> dict[int, uuid.UUID]:
    """
    Map Louvain community IDs → stable Campaign UUIDs.
    Rule: existing campaign with the largest member overlap keeps its ID.
    New communities get new Campaign rows.
    """
    # Group nodes by community
    communities: dict[int, set[str]] = defaultdict(set)
    for node_str, comm_id in partition.items():
        communities[comm_id].add(node_str)

    # Fetch existing campaign assignments for all case nodes in the partition
    all_case_ids = [uuid.UUID(n) for n in partition.keys()]
    rows = (
        await db.execute(select(Case.id, Case.campaign_id).where(Case.id.in_(all_case_ids)))
    ).fetchall()
    existing_assignments: dict[str, uuid.UUID | None] = {str(r[0]): r[1] for r in rows}

    # For each community, find best matching existing campaign by overlap
    comm_to_campaign: dict[int, uuid.UUID] = {}
    used_campaigns: set[uuid.UUID] = set()

    for comm_id, members in communities.items():
        # Count votes for each existing campaign among members
        votes: dict[uuid.UUID, int] = defaultdict(int)
        for node in members:
            existing_camp = existing_assignments.get(node)
            if existing_camp:
                votes[existing_camp] += 1

        best_campaign: uuid.UUID | None = None
        if votes:
            best_candidate = max(votes, key=lambda c: votes[c])
            if best_candidate not in used_campaigns:
                best_campaign = best_candidate
                used_campaigns.add(best_campaign)

        if best_campaign is None:
            # Create a new campaign
            new_campaign = Campaign()
            db.add(new_campaign)
            await db.flush()
            best_campaign = new_campaign.id
            used_campaigns.add(best_campaign)

        comm_to_campaign[comm_id] = best_campaign

    return comm_to_campaign


# ── Public interface ─────────────────────────────────────────────────────────


async def cluster_case(
    case_id: uuid.UUID,
    db: AsyncSession,
) -> uuid.UUID | None:
    """
    Run incremental clustering for a newly linked case.
    Returns the campaign_id assigned, or None if deferred (component too large).
    """
    case_ids, entity_ids = await _fetch_component(case_id, db)

    total_nodes = len(case_ids) + len(entity_ids)
    if total_nodes > MAX_COMPONENT_NODES:
        logger.warning(
            "component for case %s has %d nodes > %d — deferring to nightly",
            case_id,
            total_nodes,
            MAX_COMPONENT_NODES,
        )
        return None

    if len(case_ids) == 1:
        # Singleton — assign to its own campaign immediately
        rows = (
            await db.execute(select(Case.campaign_id).where(Case.id == case_id))
        ).scalar_one_or_none()
        if rows:
            return rows

        new_campaign = Campaign()
        db.add(new_campaign)
        await db.flush()
        await db.execute(update(Case).where(Case.id == case_id).values(campaign_id=new_campaign.id))
        return new_campaign.id

    # Fetch all case-entity edges in component
    ce_links = (
        await db.execute(
            select(CaseEntityLink.case_id, CaseEntityLink.entity_id).where(
                CaseEntityLink.case_id.in_(case_ids)
            )
        )
    ).fetchall()
    case_entity_edges = [(r[0], r[1]) for r in ce_links]

    # Fetch semantic edges within component
    sem_links = (
        await db.execute(
            select(SemanticLink.a_id, SemanticLink.b_id, SemanticLink.score).where(
                SemanticLink.a_id.in_(case_ids),
                SemanticLink.b_id.in_(case_ids),
                SemanticLink.score >= SEMANTIC_THRESHOLD,
            )
        )
    ).fetchall()
    semantic_edges = [(r[0], r[1], float(r[2])) for r in sem_links]

    G = _build_graph(case_ids, entity_ids, case_entity_edges, semantic_edges)
    partition = _louvain_partition(G)
    comm_to_campaign = await _reconcile_campaigns(partition, db)

    # Write campaign assignments back
    for comm_id, campaign_uuid in comm_to_campaign.items():
        members = [uuid.UUID(n) for n, c in partition.items() if c == comm_id]
        await db.execute(update(Case).where(Case.id.in_(members)).values(campaign_id=campaign_uuid))

    await db.flush()
    return comm_to_campaign.get(partition.get(str(case_id), -1))
