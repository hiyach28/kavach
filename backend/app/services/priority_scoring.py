from sqlalchemy.orm import Session
from app.models import DistrictWeeklyStat

def calculate_priority_scores(db: Session):
    """
    Computes priority_score (0-100) for all districts.
    Formula: priority_score = (volume*0.4) + (growth_rate*0.35) + (impact*0.25)
    """
    stats = db.query(DistrictWeeklyStat).all()
    if not stats:
        return
        
    max_complaints = max([s.complaint_count for s in stats]) if stats else 1
    max_loss = max([s.estimated_loss for s in stats]) if stats else 1
    
    if max_complaints == 0: max_complaints = 1
    if max_loss == 0: max_loss = 1
    
    for stat in stats:
        norm_volume = (stat.complaint_count / max_complaints) * 100
        norm_impact = (stat.estimated_loss / max_loss) * 100
        
        # Calculate growth rate and map to 0-100
        prior = stat.prior_week_complaint_count if stat.prior_week_complaint_count else 1
        growth_raw = (stat.complaint_count - prior) / prior
        # 0% growth = 50, 100% growth = 100
        growth_norm = min(max((growth_raw * 50) + 50, 0), 100)
        
        # 40/35/25 weighted split as per Deepdive requirements
        score = (norm_volume * 0.4) + (growth_norm * 0.35) + (norm_impact * 0.25)
        
        stat.priority_score = min(round(score, 2), 100.0)
        
    db.commit()
