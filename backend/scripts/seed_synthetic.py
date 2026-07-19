#!/usr/bin/env python3
"""F27: Synthetic Seed Generator — creates realistic fraud cases with ground truth.

Profiles:
    demo    ~50 cases, 3-4 campaigns, clear patterns (demo video)
    test    ~200 cases, 10+ campaigns (eval / make eval)
    load    ~5000+ cases, many campaigns (load testing)

Output:
    - Writes cases to the DB through the standard de-identify → vault → insert pipeline.
    - Writes a ground-truth manifest JSON to data/synthetic/manifest.json.
    - Ground truth includes:
        * Known campaign membership per case
        * Known fraud type per case
        * Known entity-to-campaign association

Usage:
    python backend/scripts/seed_synthetic.py --profile demo
    python backend/scripts/seed_synthetic.py --profile test
    python backend/scripts/seed_synthetic.py --profile load --count 5000
    python backend/scripts/seed_synthetic.py --profile demo --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Add backend/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.redis import close_redis_pool, init_redis_pool  # noqa: E402
from app.models.graph import Campaign, Case, CaseStatus, Entity, EntityType, FraudType, RiskLevel  # noqa: E402
from app.services.deidentify import deidentify  # noqa: E402
from app.services.pii_service import store_and_tokenize  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_synthetic")

random.seed(42)  # reproducible runs

# ── Constants ──────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
MANIFEST_PATH = SYNTHETIC_DIR / "manifest.json"

# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class SeedCase:
    fraud_type: FraudType
    risk: RiskLevel
    text: str
    district: str
    language: str
    phone: str
    upi_id: str
    campaign_name: str


@dataclass
class GroundTruthCampaign:
    name: str
    fraud_type: str
    risk: str
    case_indices: list[int]


@dataclass
class GroundTruth:
    """Known labels for evaluation."""
    total_cases: int
    campaigns: list[GroundTruthCampaign]
    seed_cases: list[dict[str, Any]]  # raw case data for benchmark

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path = MANIFEST_PATH) -> None:
        SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info("Ground truth manifest written to %s", path)


# ── Seed data ──────────────────────────────────────────────────────────────────

_PHONE_PREFIXES = [
    "98765", "99887", "98754", "98123", "98999",
    "87654", "88999", "87650", "87123", "87999",
    "76543", "77665", "76510", "76123", "76999",
]

_UPI_SUFFIXES = ["@paytm", "@gpay", "@phonepe", "@ybl", "@upi"]

_DISTRICTS = [
    "mumbai", "delhi", "bangalore", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow",
    "patna", "bhopal", "chandigarh", "guwahati", "bhubaneswar",
]

_LANGUAGES = ["hi", "en", "ta", "te", "bn"]


def _random_phone() -> str:
    return random.choice(_PHONE_PREFIXES) + f"{random.randint(0, 99999):05d}"


def _random_upi() -> str:
    name = random.choice(["user", "pay", "acct", "send", "receive", "customer", "victim", "trader"])
    num = random.randint(1, 9999)
    suffix = random.choice(_UPI_SUFFIXES)
    return f"{name}{num}{suffix}"


def _random_amount() -> str:
    amounts = [
        f"₹{random.randint(500, 50000)}",
        f"Rs {random.randint(1000, 200000)}",
        f"{random.randint(100, 5000)} rupees",
    ]
    return random.choice(amounts)


# ── Fraud-specific case generators ─────────────────────────────────────────────

_DIGITAL_ARREST_TEMPLATES = [
    "I received a call from {phone}. The caller said he is from Mumbai customs and a parcel containing drugs and passports has been caught in my name at Mumbai airport. He said I am being investigated by CBI and Narcotics Department for money laundering. He demanded {amount} for settlement and told me to transfer via {upi}. He threatened that if I don't pay, I will be arrested immediately. I was scared and transferred the money.",
    "A person claiming to be from the Cyber Crime department called me at {phone}. He said my Aadhaar card was used to open a bank account that received {amount} from illegal activities. He said the CBI has issued an arrest warrant against me. He asked me to transfer {amount} to {upi} for verification. When I said I don't have money, he asked me to take a loan. I later realized it was a scam.",
    "Got a WhatsApp call from {phone}. The person identified himself as a senior police officer from Delhi. He said my PAN card was found on a person arrested with illegal drugs worth {amount}. He said I need to pay {amount} to {upi} for an out-of-court settlement. He threatened immediate arrest if I don't comply immediately.",
    "Someone called from {phone} saying they are from the Federal Investigation Agency. They said a bank account in my name is involved in money laundering of {amount}. They asked me to transfer all my savings to {upi} for 'verification'. The call was very convincing and they had my personal details.",
    "I got a call from {phone} — the person said he is a CBI officer and a case has been filed against me in the Supreme Court for {amount} fraud. He demanded {amount} be paid via {upi} to close the case. He kept me on the phone for 3 hours and threatened to arrest my family.",
]

_JOB_FRAUD_TEMPLATES = [
    "Applied for a work from home job on Telegram. They asked for {amount} as registration fee and sent me a payment link. I paid via {upi}. Then they demanded {amount} more for training materials. After paying, they blocked me. The number they used was {phone}.",
    "Received a message offering a part-time data entry job with salary of {amount} per month. They asked me to pay {amount} as registration fee via {upi}. They called from {phone} and assured me it is refundable. After payment, they kept asking for more money.",
    "A job consultant called from {phone} offering a high-paying job in Dubai. They asked for {amount} for visa processing and ticket booking. I transferred the money to {upi}. Now their number is switched off and I have lost all my savings.",
    "Got an email about a work from home job with amazing salary. They asked me to complete some tasks and pay {amount} as deposit via {upi}. The caller from {phone} said I will earn commission on each task. I paid for 5 tasks but never received any payment back.",
    "A recruitment agency called from {phone} about a government job. They asked {amount} for application fee, exam fee, and background verification. I paid via {upi}. Later I found out the agency is fake and they have cheated many people.",
]

_INVESTMENT_FRAUD_TEMPLATES = [
    "Joined a WhatsApp group where they promised 200% returns on investment in 3 days. The group admin from {phone} said I need to invest {amount} first. I paid via {upi}. They showed me fake profit screenshots and asked me to invest more. When I asked for withdrawal, they blocked me.",
    "A trading mentor on Telegram asked me to invest in cryptocurrency through their platform. I initially invested a small amount and got returns. Then I invested {amount} via {upi}. The platform stopped working and the mentor from {phone} disappeared.",
    "Someone called from {phone} offering exclusive stock tips with guaranteed 10x returns. They asked me to pay {amount} as membership fee to their investment club. I paid via {upi}. The tips were random and I lost money in the market. They refused to refund the fee.",
    "An investment scheme promised {amount} monthly income on a one-time investment of {amount}. I transferred the money to {upi} as instructed. They called from {phone} for weeks after but then stopped answering. The website is also down now.",
    "Got a call from {phone} about a government-approved investment plan with 15% monthly interest. I invested {amount} through {upi}. The first month I got the interest, then they asked me to reinvest. Now I can't reach them and have lost {amount} total.",
]

_CUSTOMER_SUPPORT_TEMPLATES = [
    "Received a call from {phone} claiming to be Amazon customer support. They said my KYC needs to be updated otherwise my account will be blocked. They asked me to pay {amount} as verification fee via {upi}. They stole my money and my Amazon account is fine.",
    "Someone called from {phone} saying they are from my bank's customer service. They said my account will be frozen unless I complete verification. They asked me to send {amount} to {upi} as a test transaction. I lost my savings of {amount}.",
    "Got a call from {phone} — the person said my electricity bill payment of {amount} failed and I need to pay immediately through a link to avoid disconnection. I paid via {upi} but the amount was {amount} more than my actual bill. The number is now unreachable.",
    "A person claiming to be from the telecom regulator called from {phone}. He said my mobile number will be deactivated due to KYC non-compliance. He guided me to install an app and transfer {amount} to {upi} for verification. I lost my money.",
    "Received a call from {phone} claiming to be from IRCTC customer support. They said my railway ticket booking failed and I need to pay {amount} again via {upi} for rebooking. They promised refund of the first payment but it never came.",
]

_SEXTORTION_TEMPLATES = [
    "A girl sent me a friend request on Instagram. We started talking and she asked me to video call. During the call, she recorded me. Then she called from {phone} and demanded {amount} via {upi} or she will leak the video to all my contacts. I am scared and don't know what to do.",
    "Someone on a dating app convinced me to share intimate photos. Then I got a call from {phone} threatening to share them with my family and employer unless I pay {amount} to {upi}. They have been harassing me continuously for a week now.",
    "I matched with someone on a matrimonial site. After a few days of chatting, they video called me and recorded me. Now they are blackmailing me for {amount} via {upi}. They call from {phone} and have already sent screenshots to my sister.",
    "A stranger on Facebook sent me a friend request. After accepting, they video called and recorded me without my consent. They are demanding {amount} and calling from {phone}. They threatened to upload the video on YouTube and tag my family members.",
    "I received a call from {phone} saying they have hacked my phone and recorded me through the camera. They demanded {amount} in Bitcoin or UPI {upi} within 24 hours. They even quoted my correct name and address which scared me a lot.",
]

_ECOMMERCE_TEMPLATES = [
    "Ordered a mobile phone from a Facebook ad. Paid {amount} via {upi}. The product never arrived. The seller from {phone} stopped answering calls. I have been cheated of {amount}.",
    "Bought a product from an Instagram shop. They charged me {amount} via {upi} for a product that was supposed to be cash on delivery. The seller number {phone} is now switched off and the Instagram page is deleted.",
    "Someone from {phone} called offering a high-end laptop at 60% discount. I was interested and paid {amount} as advance via {upi}. They promised delivery in 3 days but it's been 2 weeks. Now they are not responding.",
    "A fake OLX buyer sent me a payment link saying they have paid for my listed item. I clicked the link and entered my UPI PIN. {amount} was deducted from my account. The person called from {phone} but the number is now unreachable.",
    "Got a message about a lucky draw winner. They said I won {amount} in prize money. To claim it, I needed to pay {amount} as processing fee via {upi}. I paid but never received any prize. The caller from {phone} has disappeared.",
]

# Map fraud types to their templates
_FRAUD_GENERATORS: dict[tuple[FraudType, RiskLevel], list[str]] = {
    (FraudType.digital_arrest, RiskLevel.danger): _DIGITAL_ARREST_TEMPLATES,
    (FraudType.job_fraud, RiskLevel.suspicious): _JOB_FRAUD_TEMPLATES,
    (FraudType.investment_fraud, RiskLevel.danger): _INVESTMENT_FRAUD_TEMPLATES,
    (FraudType.customer_support, RiskLevel.suspicious): _CUSTOMER_SUPPORT_TEMPLATES,
    (FraudType.sextortion, RiskLevel.danger): _SEXTORTION_TEMPLATES,
    (FraudType.ecommerce, RiskLevel.suspicious): _ECOMMERCE_TEMPLATES,
}

# ── Campaign definitions with ground truth ─────────────────────────────────────

@dataclass
class CampaignDef:
    name: str
    fraud_type: FraudType
    risk: RiskLevel
    phone: str
    upi: str
    case_count: int


_DEMO_CAMPAIGNS = [
    CampaignDef("Digital Arrest Ring — Mumbai", FraudType.digital_arrest, RiskLevel.danger,
                phone="9876543210", upi="paynow@paytm", case_count=15),
    CampaignDef("Job Fraud Syndicate — Delhi", FraudType.job_fraud, RiskLevel.suspicious,
                phone="9988776655", upi="jobfee@ybl", case_count=10),
    CampaignDef("Investment Scam Group", FraudType.investment_fraud, RiskLevel.danger,
                phone="9876512345", upi="crypto@upi", case_count=12),
    CampaignDef("Support Scam Call Center", FraudType.customer_support, RiskLevel.suspicious,
                phone="8765432109", upi="kycfee@gpay", case_count=8),
]

_TEST_CAMPAIGNS = [
    CampaignDef("Digital Arrest — North", FraudType.digital_arrest, RiskLevel.danger,
                phone="9876540001", upi="arrest1@paytm", case_count=20),
    CampaignDef("Digital Arrest — South", FraudType.digital_arrest, RiskLevel.danger,
                phone="9876540002", upi="arrest2@phonepe", case_count=18),
    CampaignDef("Job Fraud — IT Sector", FraudType.job_fraud, RiskLevel.suspicious,
                phone="9988770001", upi="job1@ybl", case_count=15),
    CampaignDef("Job Fraud — Govt Sector", FraudType.job_fraud, RiskLevel.suspicious,
                phone="9988770002", upi="jobgovt@paytm", case_count=12),
    CampaignDef("Trading Guru", FraudType.investment_fraud, RiskLevel.danger,
                phone="9876510001", upi="trade1@upi", case_count=22),
    CampaignDef("Crypto King", FraudType.investment_fraud, RiskLevel.danger,
                phone="9876510002", upi="crypto1@upi", case_count=18),
    CampaignDef("Bank Support Ring", FraudType.customer_support, RiskLevel.suspicious,
                phone="8765430001", upi="bank1@gpay", case_count=14),
    CampaignDef("Telecom KYC Scam", FraudType.customer_support, RiskLevel.suspicious,
                phone="8765430002", upi="kyc1@gpay", case_count=12),
    CampaignDef("Instagram Blackmail", FraudType.sextortion, RiskLevel.danger,
                phone="7654310001", upi="blackmail@phonepe", case_count=10),
    CampaignDef("Facebook Marketplace Fraud", FraudType.ecommerce, RiskLevel.suspicious,
                phone="7654320001", upi="order1@gpay", case_count=14),
    CampaignDef("OLX Payment Scam", FraudType.ecommerce, RiskLevel.suspicious,
                phone="7654320002", upi="olxpay@paytm", case_count=10),
]

_LOAD_CAMPAIGNS: list[CampaignDef] = [
    CampaignDef(f"Campaign #{i}", random.choice(list(_FRAUD_GENERATORS.keys()))[0],
                random.choice(list(_FRAUD_GENERATORS.keys()))[1],
                phone=_random_phone(), upi=_random_upi(),
                case_count=random.randint(30, 80))
    for i in range(30)
]


# ── Seed generation ────────────────────────────────────────────────────────────

def _fill_template(template: str, phone: str, upi: str) -> str:
    """Fill a template with random values."""
    amount = _random_amount()
    return template.format(phone=phone, upi=upi, amount=amount)


def _generate_seed_cases(
    campaigns: list[CampaignDef],
    base_templates: dict[tuple[FraudType, RiskLevel], list[str]],
) -> list[SeedCase]:
    """Generate a list of seed cases from campaign definitions."""
    seed_cases: list[SeedCase] = []
    for camp in campaigns:
        templates = base_templates.get((camp.fraud_type, camp.risk), _ECOMMERCE_TEMPLATES)
        for _ in range(camp.case_count):
            template = random.choice(templates)
            text = _fill_template(template, camp.phone, camp.upi)
            seed_cases.append(SeedCase(
                fraud_type=camp.fraud_type,
                risk=camp.risk,
                text=text,
                district=random.choice(_DISTRICTS),
                language=random.choice(_LANGUAGES),
                phone=camp.phone,
                upi_id=camp.upi,
                campaign_name=camp.name,
            ))
    return seed_cases


async def seed_database(
    seed_cases: list[SeedCase],
    campaigns: list[CampaignDef],
    *,
    dry_run: bool = False,
    enqueue: bool = False,
) -> GroundTruth:
    """Write seed cases to the database through the standard pipeline.

    Returns a GroundTruth object that can be written to a manifest file.
    """
    if dry_run:
        logger.info("Dry-run: %d cases validated, none written.", len(seed_cases))
        # Still build and return ground truth
        gt = _build_ground_truth(seed_cases, campaigns)
        return gt

    pii_key = settings.PII_MASTER_KEY.encode("utf-8").ljust(32, b"\0")[:32]

    if enqueue:
        await init_redis_pool()

    from app.core.redis import redis_pool as rp

    campaign_map: dict[str, uuid.UUID] = {}
    inserted = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        # 1. Create campaign rows
        for camp in campaigns:
            new_campaign = Campaign(
                label=camp.name,
                velocity=random.uniform(1.0, 8.0),
                projected_victims=random.randint(camp.case_count, camp.case_count * 5),
            )
            db.add(new_campaign)
            await db.flush()
            campaign_map[camp.name] = new_campaign.id

        # 2. Create cases through the pipeline
        for idx, seed in enumerate(seed_cases):
            try:
                case_id = uuid.uuid4()
                camp_id = campaign_map.get(seed.campaign_name)

                # a. De-identify
                deid_result = deidentify(seed.text)

                # b. Vault PII
                if deid_result["extracted"]:
                    await store_and_tokenize(
                        deid_result["extracted"], case_id, db, pii_key,
                    )

                # c. Insert case with known ground-truth labels
                new_case = Case(
                    id=case_id,
                    status=CaseStatus.clustered,  # skip re-processing
                    fraud_type=seed.fraud_type,
                    risk=seed.risk,
                    confidence=0.92,
                    campaign_id=camp_id,
                    district=seed.district,
                    language=seed.language,
                )
                db.add(new_case)

                # d. Optionally enqueue for re-processing
                if enqueue and rp:
                    await rp.enqueue_job(
                        "process_case",
                        case_id=str(case_id),
                        masked_text=deid_result["masked_text"],
                    )

                inserted += 1

            except Exception as exc:
                logger.error("Error seeding case %d: %s", idx, exc)
                errors += 1

            # Periodic flush
            if idx % 50 == 0 and idx > 0:
                await db.flush()
                logger.info("  Flushed %d/%d cases", idx, len(seed_cases))

        await db.commit()

    if enqueue:
        await close_redis_pool()

    logger.info("Database seeded: %d inserted, %d errors", inserted, errors)

    ground_truth = _build_ground_truth(seed_cases, campaigns)
    ground_truth.write()
    return ground_truth


def _build_ground_truth(
    seed_cases: list[SeedCase],
    campaigns: list[CampaignDef],
) -> GroundTruth:
    """Build ground truth manifest from seed data."""
    case_data = []
    start_idx = 0
    gt_campaigns = []

    for camp in campaigns:
        indices = list(range(start_idx, start_idx + camp.case_count))
        gt_campaigns.append(GroundTruthCampaign(
            name=camp.name,
            fraud_type=camp.fraud_type.value,
            risk=camp.risk.value,
            case_indices=indices,
        ))
        start_idx += camp.case_count

    for idx, seed in enumerate(seed_cases):
        case_data.append({
            "index": idx,
            "fraud_type": seed.fraud_type.value,
            "risk": seed.risk.value,
            "campaign": seed.campaign_name,
            "district": seed.district,
            "language": seed.language,
            "phone": seed.phone,
            "upi": seed.upi_id,
            "text_preview": seed.text[:100] + "...",
        })

    return GroundTruth(
        total_cases=len(seed_cases),
        campaigns=gt_campaigns,
        seed_cases=case_data,
    )


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="KAVACH synthetic seed generator")
    parser.add_argument("--profile", choices=["demo", "test", "load"], default="demo",
                        help="Seed profile (default: demo)")
    parser.add_argument("--count", type=int, default=0,
                        help="Override case count (load profile default: 5000)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate ground truth only, skip DB write")
    parser.add_argument("--enqueue", action="store_true",
                        help="Enqueue worker jobs (requires Redis)")
    parser.add_argument("--campaigns", type=int, default=0,
                        help="Override campaign count (load profile only)")
    args = parser.parse_args()

    # Select profile
    if args.profile == "demo":
        campaigns_list = _DEMO_CAMPAIGNS
        if args.count:
            # Scale each campaign proportionally
            ratio = args.count / sum(c.case_count for c in _DEMO_CAMPAIGNS)
            for c in campaigns_list:
                c.case_count = max(1, int(c.case_count * ratio))
    elif args.profile == "test":
        campaigns_list = _TEST_CAMPAIGNS
        if args.count:
            ratio = args.count / sum(c.case_count for c in _TEST_CAMPAIGNS)
            for c in campaigns_list:
                c.case_count = max(1, int(c.case_count * ratio))
    else:  # load
        num_campaigns = args.campaigns or 30
        campaigns_list = [
            CampaignDef(f"LoadCamp #{i}", random.choice(list(_FRAUD_GENERATORS.keys()))[0],
                        random.choice(list(_FRAUD_GENERATORS.keys()))[1],
                        phone=_random_phone(), upi=_random_upi(),
                        case_count=random.randint(30, 80))
            for i in range(num_campaigns)
        ]
        if args.count:
            # Distribute count across campaigns
            per_camp = max(5, args.count // len(campaigns_list))
            for c in campaigns_list:
                c.case_count = per_camp

    total_expected = sum(c.case_count for c in campaigns_list)
    logger.info("Profile: %s", args.profile)
    logger.info("Campaigns: %d", len(campaigns_list))
    logger.info("Cases to generate: %d", total_expected)

    seed_cases = _generate_seed_cases(campaigns_list, _FRAUD_GENERATORS)
    logger.info("Generated %d seed cases", len(seed_cases))

    ground_truth = asyncio.run(seed_database(
        seed_cases, campaigns_list,
        dry_run=args.dry_run,
        enqueue=args.enqueue,
    ))

    logger.info("Ground truth campaigns: %d", len(ground_truth.campaigns))
    if not args.dry_run:
        logger.info("Database seeded successfully!")
    else:
        logger.info("Dry-run complete. Ground truth written to %s", MANIFEST_PATH)


if __name__ == "__main__":
    main()
