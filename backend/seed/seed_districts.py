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

    districts_data = [
        {"name": "Mumbai", "state": "Maharashtra", "complaints": 120, "prior": 100, "loss": 5000000},
        {"name": "Delhi", "state": "Delhi", "complaints": 200, "prior": 250, "loss": 8000000},
        {"name": "Bangalore", "state": "Karnataka", "complaints": 150, "prior": 85, "loss": 7000000},
        {"name": "Jamtara", "state": "Jharkhand", "complaints": 40, "prior": 15, "loss": 10000000}, 
        {"name": "Pune", "state": "Maharashtra", "complaints": 80, "prior": 80, "loss": 2000000},
        {"name": "Hyderabad", "state": "Telangana", "complaints": 110, "prior": 90, "loss": 4500000},
        {"name": "Chennai", "state": "Tamil Nadu", "complaints": 95, "prior": 95, "loss": 3000000},
        {"name": "Kolkata", "state": "West Bengal", "complaints": 105, "prior": 130, "loss": 2500000},
        {"name": "Ahmedabad", "state": "Gujarat", "complaints": 70, "prior": 50, "loss": 6000000},
        {"name": "Jaipur", "state": "Rajasthan", "complaints": 65, "prior": 60, "loss": 1500000},
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
