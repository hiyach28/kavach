from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import GraphResponse, GraphData, NodeSchema, LinkSchema, CampaignSchema
from app.models import Case, Campaign, CaseInfraLink

router = APIRouter()

@router.get("/graph", response_model=GraphResponse)
def get_graph(db: Session = Depends(get_db)):
    cases = db.query(Case).filter(Case.status == "classified").all()
    campaigns_db = db.query(Campaign).all()
    infra_links = db.query(CaseInfraLink).all()
    
    nodes = []
    for c in cases:
        degree = len([l for l in infra_links if l.case_id == c.id])
        nodes.append(NodeSchema(
            id=f"case_{c.id}",
            label=f"Case {c.id}",
            group=f"campaign_{c.campaign_id}" if c.campaign_id else "unclustered",
            degree=degree if degree > 0 else 1,
            fraud_type=c.fraud_type
        ))
        
    links = []
    infra_map = {}
    for l in infra_links:
        infra_map.setdefault(l.infra_node_id, []).append(l.case_id)
        
    for infra, c_ids in infra_map.items():
        if len(c_ids) > 1:
            for i in range(len(c_ids)):
                for j in range(i+1, len(c_ids)):
                    links.append(LinkSchema(
                        source=f"case_{c_ids[i]}",
                        target=f"case_{c_ids[j]}",
                        type="shared_infra"
                    ))
                    
    campaigns = [CampaignSchema(
        id=camp.id,
        label=camp.label,
        case_count=camp.case_count,
        total_estimated_loss=camp.total_estimated_loss
    ) for camp in campaigns_db]
    
    return GraphResponse(
        success=True,
        data=GraphData(
            nodes=nodes,
            links=links,
            campaigns=campaigns
        )
    )
