import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app.models import District, DistrictWeeklyStat
from app.services.priority_scoring import calculate_priority_scores

def seed_districts():
    db = SessionLocal()
    
    db.query(DistrictWeeklyStat).delete()
    db.query(District).delete()
    db.commit()

    # Using NCRB 2023 Cybercrime statistics as a baseline (Total ~86,420 cases)
    # Total estimated loss roughly represents the ₹1,935 crore reported by MHA for digital arrests/major fraud
    districts_data = [
        {"name": "Bengaluru", "state": "Karnataka", "complaints": 15489, "prior": 14200, "loss": 4500000000},
        {"name": "Hyderabad", "state": "Telangana", "complaints": 12236, "prior": 11500, "loss": 3200000000},
        {"name": "Noida", "state": "Uttar Pradesh", "complaints": 6794, "prior": 6100, "loss": 1800000000},
        {"name": "Mumbai", "state": "Maharashtra", "complaints": 4800, "prior": 4300, "loss": 2500000000},
        {"name": "Delhi", "state": "Delhi", "complaints": 3500, "prior": 3200, "loss": 1200000000},
        {"name": "Pune", "state": "Maharashtra", "complaints": 2800, "prior": 2900, "loss": 850000000},
        {"name": "Patna", "state": "Bihar", "complaints": 3100, "prior": 2800, "loss": 500000000},
        {"name": "Jamtara", "state": "Jharkhand", "complaints": 850, "prior": 600, "loss": 1500000000}, 
        {"name": "Chennai", "state": "Tamil Nadu", "complaints": 2100, "prior": 1950, "loss": 900000000},
        {"name": "Kolkata", "state": "West Bengal", "complaints": 2600, "prior": 2800, "loss": 1100000000},
    ]

    for d in districts_data:
        dist = District(name=d["name"], state=d["state"], geojson_id=d["name"])
        db.add(dist)
        db.commit()
        
        stat = DistrictWeeklyStat(
            district_name=d["name"],
            week_start=date.today(),
            complaint_count=d["complaints"],
            prior_week_complaint_count=d["prior"],
            estimated_loss=d["loss"]
        )
        db.add(stat)
        
    db.commit()
    
    calculate_priority_scores(db)
    print("Districts seeded and scored. 10 Districts loaded.")
    db.close()

if __name__ == "__main__":
    seed_districts()
