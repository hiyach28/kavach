import networkx as nx
import community as community_louvain
import json
import numpy as np
from sqlalchemy.orm import Session
from app.models import Case, Campaign, CaseInfraLink, CaseSemanticLink
from datetime import datetime, timezone

def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def recluster_campaigns(db: Session):
    """
    Re-runs Louvain clustering on the graph of Cases linked by shared InfraNodes.
    Updates the cases' campaign_id and the Campaign aggregate stats.
    """
    G = nx.Graph()
    
    # Get all cases that are classified
    cases = db.query(Case).filter(Case.status == "classified").all()
    for case in cases:
        G.add_node(case.id)
        
    # Get all infra links
    infra_links = db.query(CaseInfraLink).all()
    
    # Map infra_node_id to a list of case_ids
    infra_to_cases = {}
    for link in infra_links:
        infra_to_cases.setdefault(link.infra_node_id, []).append(link.case_id)
        
    # Add infra edges between cases sharing an infra node
    for infra_id, c_ids in infra_to_cases.items():
        if len(c_ids) > 1:
            for i in range(len(c_ids)):
                for j in range(i + 1, len(c_ids)):
                    G.add_edge(c_ids[i], c_ids[j], type='infra')

    # Add semantic edges based on embeddings
    # 1. Parse embeddings
    case_embeddings = {}
    for case in cases:
        if case.embedding:
            try:
                emb = json.loads(case.embedding)
                if emb and len(emb) > 0:
                    case_embeddings[case.id] = np.array(emb)
            except:
                pass

    # Clear old semantic links
    db.query(CaseSemanticLink).delete()
    
    # 2. Compute similarity
    case_ids = list(case_embeddings.keys())
    for i in range(len(case_ids)):
        for j in range(i + 1, len(case_ids)):
            c1 = case_ids[i]
            c2 = case_ids[j]
            sim = cosine_similarity(case_embeddings[c1], case_embeddings[c2])
            if sim > 0.85:
                # Add to NetworkX graph to allow semantic clustering
                if not G.has_edge(c1, c2):
                    G.add_edge(c1, c2, type='semantic')
                # Save to DB for frontend visualization
                db.add(CaseSemanticLink(
                    source_case_id=c1,
                    target_case_id=c2,
                    similarity_score=float(sim)
                ))
    
    if len(G.nodes) == 0:
        return
        
    # Run Louvain clustering
    partition = community_louvain.best_partition(G)
    
    campaign_aggregates = {}
    
    for case_id, comm_id in partition.items():
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            continue
            
        # Ensure campaign exists
        campaign = db.query(Campaign).filter(Campaign.id == comm_id).first()
        if not campaign:
            campaign = Campaign(
                id=comm_id, 
                label=f"Campaign {comm_id}", 
                last_clustered_at=datetime.now(timezone.utc)
            )
            db.add(campaign)
            db.commit()
            
        case.campaign_id = comm_id
        
        # Aggregate logic
        if comm_id not in campaign_aggregates:
            campaign_aggregates[comm_id] = {"count": 0, "loss": 0}
            
        campaign_aggregates[comm_id]["count"] += 1
        if case.risk_score:
             # Heuristic: $1k loss per risk score point
             campaign_aggregates[comm_id]["loss"] += (case.risk_score * 1000)

    # Update campaigns
    from app.services.network_intelligence import compute_takedown_brief
    for comm_id, agg in campaign_aggregates.items():
        camp = db.query(Campaign).filter(Campaign.id == comm_id).first()
        if camp:
            camp.case_count = agg["count"]
            camp.total_estimated_loss = agg["loss"]
            camp.last_clustered_at = datetime.now(timezone.utc)
            
            # Compute takedown metrics
            brief = compute_takedown_brief(db, camp.id)
            if brief:
                camp.cross_jurisdiction = brief["cross_jurisdiction"]
                camp.primary_target_infra_id = brief["primary_target_infra_id"]
                camp.primary_target_betweenness = brief["primary_target_betweenness"]
                camp.pct_connectivity_lost = brief["pct_connectivity_lost"]
                camp.fractures_network = brief["fractures_network"]
            
    db.commit()
