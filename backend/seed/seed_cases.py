import sys
import os
import uuid
import json
import hashlib
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app.models import Case, Campaign, CaseRedFlag, InfraNode, CaseInfraLink
from app.services.clustering import recluster_campaigns

def seed_cases():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    db.query(CaseInfraLink).delete()
    db.query(CaseRedFlag).delete()
    db.query(Case).delete()
    db.query(Campaign).delete()
    db.query(InfraNode).delete()
    db.commit()

    # Campaign 1: Digital Arrest Ring (Shared Bank Account)
    bank_acc = "HDFC000123456789"
    bank_hash = hashlib.sha256(bank_acc.encode()).hexdigest()
    node1 = InfraNode(type="bank_account", value_hash=bank_hash)
    db.add(node1)
    db.commit()

    for i in range(5):
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=f"Received a call from CBI saying my Aadhaar is linked to money laundering. They asked me to transfer funds to [BANK_ACC_1] for verification.",
            pii_token_map=json.dumps({"[BANK_ACC_1]": bank_acc}),
            fraud_type="digital_arrest",
            risk_score=95 - i,
            confidence=0.9,
            verdict="High confidence digital arrest scam.",
            reporting_portal="https://cybercrime.gov.in",
            district="Mumbai",
            status="classified"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        link = CaseInfraLink(case_id=case.id, infra_node_id=node1.id)
        db.add(link)

    # Campaign 2: Investment Scam (Shared Phone)
    phone = "+919876543210"
    phone_hash = hashlib.sha256(phone.encode()).hexdigest()
    node2 = InfraNode(type="phone", value_hash=phone_hash)
    db.add(node2)
    db.commit()

    for i in range(6):
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=f"Joined a telegram group where admin [PHONE_1] promised 200% returns on crypto.",
            pii_token_map=json.dumps({"[PHONE_1]": phone}),
            fraud_type="investment_fraud",
            risk_score=80 + i,
            confidence=0.85,
            verdict="Typical investment/crypto scam pattern.",
            reporting_portal="https://cybercrime.gov.in",
            district="Delhi",
            status="classified"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        link = CaseInfraLink(case_id=case.id, infra_node_id=node2.id)
        db.add(link)

    # Campaign 3: OTP/SIM Swap Ring (Shared Email)
    email = "fake.support@paytm-kyc.com"
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    node3 = InfraNode(type="email", value_hash=email_hash)
    db.add(node3)
    db.commit()

    for i in range(7):
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=f"Got an email from [EMAIL_1] saying my KYC is expired. I clicked the link and entered my OTP, lost Rs 50000.",
            pii_token_map=json.dumps({"[EMAIL_1]": email}),
            fraud_type="otp_sim_swap",
            risk_score=75 + i,
            confidence=0.9,
            verdict="Phishing/KYC expired OTP scam.",
            reporting_portal="https://cybercrime.gov.in",
            district="Jamtara",
            status="classified"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        link = CaseInfraLink(case_id=case.id, infra_node_id=node3.id)
        db.add(link)

    # Campaign 4: Courier/Parcel Scam (Shared Device ID)
    device = "device_fingerprint_8f9a2b"
    device_hash = hashlib.sha256(device.encode()).hexdigest()
    node4 = InfraNode(type="device_id", value_hash=device_hash)
    db.add(node4)
    db.commit()

    for i in range(10):
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=f"Received SMS that my FedEx package is stuck at customs. Clicked [URL_1] and lost Rs 10000.",
            pii_token_map=json.dumps({"[URL_1]": "http://fedex-customs-track.com"}),
            fraud_type="courier_parcel",
            risk_score=60 + i,
            confidence=0.8,
            verdict="Common FedEx/Customs parcel scam.",
            reporting_portal="https://cybercrime.gov.in",
            district="Bangalore",
            status="classified"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        link = CaseInfraLink(case_id=case.id, infra_node_id=node4.id)
        db.add(link)

    # Campaign 5: Job Fraud (Shared WhatsApp Number)
    wa_phone = "+917777777777"
    wa_hash = hashlib.sha256(wa_phone.encode()).hexdigest()
    node5 = InfraNode(type="phone", value_hash=wa_hash)
    db.add(node5)
    db.commit()

    for i in range(8):
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=f"Got a WhatsApp from [PHONE_1] offering WFH job liking YouTube videos. Paid 5000 as registration fee.",
            pii_token_map=json.dumps({"[PHONE_1]": wa_phone}),
            fraud_type="job_loan_scam",
            risk_score=50 + i,
            confidence=0.95,
            verdict="YouTube like/subscribe task fraud.",
            reporting_portal="https://cybercrime.gov.in",
            district="Pune",
            status="classified"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        link = CaseInfraLink(case_id=case.id, infra_node_id=node5.id)
        db.add(link)

    db.commit()
    
    recluster_campaigns(db)
    print("Seed complete. 36 Cases and 5 clusters generated.")
    db.close()

if __name__ == "__main__":
    seed_cases()
