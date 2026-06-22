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
        script_variations = [
            f"I received an automated call claiming to be from FedEx stating my parcel to Taiwan was blocked. When I pressed 1, it connected me to a person claiming to be a Customs officer. They said my parcel contained 5 expired passports and MDMA. They transferred my call to a 'Cyber Crime Police' officer who demanded I join a Skype video call. On the call, a man in uniform showed me a fake CBI ID and a forged Supreme Court arrest warrant. He claimed my Aadhaar was linked to money laundering and human trafficking. I was put under 'Digital Arrest' and told not to disconnect the call or talk to anyone. They instructed me to transfer ₹2,50,000 to a 'secret RBI verification account' ({bank_acc}) to clear my name. After the transfer, they disconnected the call.",
            f"Got a WhatsApp audio call from an unknown number. The caller said he was an officer from Mumbai Police Cyber Cell. He told me that an illegal parcel containing drugs was booked under my name using my Aadhaar card. He said my bank accounts were frozen and I was under digital arrest. He forced me to download Skype for an interrogation. During the video call, he was sitting in what looked like a real police station. He forced me to send Rs 5 Lakhs to {bank_acc} as a 'security deposit' which he promised would be refunded after verification.",
            f"An IVR call from 'TRAI' informed me that my mobile number would be disconnected in 2 hours due to illegal activities. I was connected to an executive who said my Aadhaar was used to buy 9 SIM cards in Mumbai for terrorist activities. He transferred the call to 'CBI Headquarters'. A person acting as a CBI officer put me under digital arrest on a WhatsApp video call. He sent me an official-looking NDA (Non-Disclosure Agreement) and demanded that I transfer all my savings to an RBI safe account {bank_acc} to prevent immediate physical arrest.",
            f"I was contacted by someone claiming to be from the Enforcement Directorate (ED). They alleged my bank account was involved in an international money laundering syndicate. They initiated a 'digital arrest' over Skype, displaying fake ED badges and a forged arrest warrant with my photo on it. I was coerced into transferring ₹8,000,000 to their 'investigation account' ({bank_acc}) to verify my funds were legal. They stayed on the call for 8 hours straight so I couldn't contact my family.",
            f"FedEx customer service called about a package destined for Iran containing contraband. The call was routed to a 'narcotics officer' who told me I was a prime suspect in a drug cartel case. I was placed under digital arrest via video call. The officer threatened me with 10 years in jail and forced me to transfer ₹12 Lakhs to a government escrow account ({bank_acc}) to secure bail."
        ]

        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=script_variations[i % len(script_variations)].replace(bank_acc, "[BANK_ACC_1]"),
            pii_token_map=json.dumps({"[BANK_ACC_1]": bank_acc}),
            fraud_type="digital_arrest",
            risk_score=95 - i,
            confidence=0.92,
            verdict="High confidence digital arrest scam. Matches MHA advisory patterns of fake customs and CBI impersonation.",
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
        inv_script = f"I was added to a Telegram group named 'Stock Market Premium Tips' by an admin {phone}. They shared screenshots of huge profits and persuaded me to invest in an Institutional Trading Account. I clicked the link and deposited Rs 50,000. For two days, the dashboard showed my portfolio growing to Rs 1,50,000. But when I tried to withdraw, they demanded a 20% 'capital gains tax' upfront. I paid it, but they blocked my number."
        
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=inv_script.replace(phone, "[PHONE_1]"),
            pii_token_map=json.dumps({"[PHONE_1]": phone}),
            fraud_type="investment_fraud",
            risk_score=80 + i,
            confidence=0.85,
            verdict="Typical investment/crypto scam pattern with fake profit dashboard and withdrawal fee extortion.",
            reporting_portal="https://cybercrime.gov.in",
            district="Bengaluru",
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
        otp_variations = [
            f"Got an email from {email} saying my PAN card was deactivated for YONO SBI login. I clicked the link, it asked for my PAN number and an OTP. I submitted the OTP and Rs 85,000 was debited in 3 transactions.",
            f"Received a call claiming my Jio SIM would be blocked as I hadn't completed my 5G KYC. They emailed me a link from {email}. I downloaded an APK file from there. Within 10 minutes, Rs 1.2 Lakhs was swept from my ICICI account without me even entering an OTP.",
            f"I got a WhatsApp message with an electricity bill disconnection notice. The contact email was {email}. They asked me to pay Rs 10 as a test payment. As soon as I entered the OTP on the payment gateway, my entire salary account was emptied.",
            f"Received an email from {email} appearing to be from HDFC Bank rewards department. They said I had 50,000 unredeemed reward points. To claim them, I entered my card details and the OTP sent to my phone. Later I saw a transaction of Rs 40,000 on my credit card."
        ]
        
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=otp_variations[i % len(otp_variations)].replace(email, "[EMAIL_1]"),
            pii_token_map=json.dumps({"[EMAIL_1]": email}),
            fraud_type="otp_sim_swap",
            risk_score=75 + i,
            confidence=0.9,
            verdict="Phishing/KYC expired OTP scam with urgency triggers.",
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
        url = "http://fedex-customs-track.com"
        courier_variations = [
            f"Received SMS that my BlueDart package address is incorrect. Clicked {url} and paid Rs 5 for address update. Next day my account was hacked.",
            f"Got a message saying 'Your India Post parcel is waiting for delivery. Update info at {url}'. Lost Rs 15,000.",
            f"An automated voice told me my FedEx parcel was flagged. I clicked the tracking link {url} and they installed a screen sharing app.",
        ]
        
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=courier_variations[i % len(courier_variations)].replace(url, "[URL_1]"),
            pii_token_map=json.dumps({"[URL_1]": url}),
            fraud_type="courier_parcel",
            risk_score=60 + i,
            confidence=0.8,
            verdict="Common delivery/Customs parcel phishing scam.",
            reporting_portal="https://cybercrime.gov.in",
            district="Bengaluru",
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
        job_variations = [
            f"Got a WhatsApp message from {wa_phone} offering a part-time WFH job liking YouTube videos. They paid me Rs 150 initially to gain trust. Then they added me to a Telegram group and gave me 'Prepaid Tasks' where I had to deposit money to get higher returns. I deposited Rs 1.5 Lakhs but couldn't withdraw.",
            f"Saw an Instagram ad for Amazon data entry jobs. Contacted the number {wa_phone}. They asked for a Rs 2,500 registration fee. Then they said my account was frozen and I need to pay 18% GST to unfreeze it. Lost Rs 45,000 total.",
            f"Someone from {wa_phone} contacted me on Telegram saying they were HR from a reputed MNC. They gave me a link to rate hotels on Google Maps. After 3 free tasks, they forced me to buy 'VIP crypto tasks' to continue. I lost all my savings.",
            f"Applied for a personal loan online. Got a call from {wa_phone} saying my loan was approved but I need to pay file charges, processing fees, and advance EMI. Transferred Rs 35,000 to them, then they blocked my number."
        ]
        
        audit_id = str(uuid.uuid4())
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=job_variations[i % len(job_variations)].replace(wa_phone, "[PHONE_1]"),
            pii_token_map=json.dumps({"[PHONE_1]": wa_phone}),
            fraud_type="job_loan_scam",
            risk_score=50 + i,
            confidence=0.95,
            verdict="Classic prepaid task / job fraud scam pattern.",
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
