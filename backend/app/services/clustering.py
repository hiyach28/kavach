import networkx as nx
import community as community_louvain
from sqlalchemy.orm import Session
from app.models import Case, Campaign, CaseInfraLink
from datetime import datetime, timezone

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
        
    # Add edges between cases sharing an infra node
    for infra_id, c_ids in infra_to_cases.items():
        if len(c_ids) > 1:
            for i in range(len(c_ids)):
                for j in range(i + 1, len(c_ids)):
                    G.add_edge(c_ids[i], c_ids[j])
                    
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
    for comm_id, agg in campaign_aggregates.items():
        camp = db.query(Campaign).filter(Campaign.id == comm_id).first()
        if camp:
            camp.case_count = agg["count"]
            camp.total_estimated_loss = agg["loss"]
            camp.last_clustered_at = datetime.now(timezone.utc)
            
    db.commit()
