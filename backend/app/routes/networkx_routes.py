from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import GraphResponse, GraphData, NodeSchema, LinkSchema, CampaignSchema
from app.models import Case, Campaign, InfraNode, CaseInfraLink, CaseSemanticLink

router = APIRouter()

@router.get("/graph", response_model=GraphResponse)
def get_graph(db: Session = Depends(get_db)):
    cases = db.query(Case).all()  # Include all cases, not just classified
    campaigns_db = db.query(Campaign).all()
    infra_links = db.query(CaseInfraLink).all()
    
    # Build node set — all case IDs as strings
    case_id_set = {c.id for c in cases}
    node_id_set = {f"case_{c.id}" for c in cases}
    
    nodes = []
    for c in cases:
        degree = len([l for l in infra_links if l.case_id == c.id])
        nodes.append(NodeSchema(
            id=f"case_{c.id}",
            label=f"Case {c.id}",
            group=f"campaign_{c.campaign_id}" if c.campaign_id else "unclustered",
            degree=max(degree, 1),
            fraud_type=c.fraud_type
        ))
        
    links = []
    infra_map = {}
    for l in infra_links:
        # Only include if case is in our node set
        if l.case_id in case_id_set:
            infra_map.setdefault(l.infra_node_id, []).append(l.case_id)
        
    for infra, c_ids in infra_map.items():
        if len(c_ids) > 1:
            for i in range(len(c_ids)):
                for j in range(i+1, len(c_ids)):
                    src = f"case_{c_ids[i]}"
                    tgt = f"case_{c_ids[j]}"
                    # Only add link if both nodes exist
                    if src in node_id_set and tgt in node_id_set:
                        links.append(LinkSchema(
                            source=src,
                            target=tgt,
                            type="shared_infra"
                        ))
                    
    campaigns = [CampaignSchema(
        id=camp.id,
        label=camp.label,
        case_count=camp.case_count,
        total_estimated_loss=camp.total_estimated_loss,
        cross_jurisdiction=camp.cross_jurisdiction,
        primary_target_infra_id=camp.primary_target_infra_id,
        primary_target_betweenness=camp.primary_target_betweenness,
        pct_connectivity_lost=camp.pct_connectivity_lost,
        fractures_network=camp.fractures_network
    ) for camp in campaigns_db]
    
    # Semantic Links — use LinkSchema (drop similarity field, it's not in schema)
    semantic_links_db = db.query(CaseSemanticLink).all()
    for sl in semantic_links_db:
        src = f"case_{sl.source_case_id}"
        tgt = f"case_{sl.target_case_id}"
        if src in node_id_set and tgt in node_id_set:
            links.append(LinkSchema(
                source=src,
                target=tgt,
                type="semantic"
            ))
        
    return GraphResponse(
        success=True,
        data=GraphData(
            nodes=nodes,
            links=links,
            campaigns=campaigns
        )
    )
