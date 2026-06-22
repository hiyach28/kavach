import uuid
import time
import json
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ClassifyRequest, ClassifyResponse, CaseResponseData, RedFlagSchema
from app.models import Case, AuditLog, CaseRedFlag, InfraNode, CaseInfraLink
from app.deidentify import deidentify_text
from app.llm_client import classify_text_gemini, get_embedding
from app.services.clustering import recluster_campaigns

router = APIRouter()

@router.post("/classify", response_model=ClassifyResponse)
def classify_text(request: ClassifyRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    audit_id = str(uuid.uuid4())
    
    # 1. De-identify
    safe_text, token_map = deidentify_text(request.raw_text)
    
    # Audit log creation
    audit = AuditLog(
        audit_id=audit_id,
        event="classify_attempt",
        request_payload=safe_text
    )
    db.add(audit)
    db.commit()
    
    # 2. LLM Classification
    llm_result = classify_text_gemini(safe_text)
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    if not llm_result:
        # Fallback graceful degradation
        db.add(AuditLog(audit_id=audit_id, event="classify_failure"))
        db.commit()
        
        # Save degraded case
        case = Case(
            audit_id=audit_id,
            raw_text_deidentified=safe_text,
            pii_token_map=token_map,
            status="needs_manual_review"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        
        return ClassifyResponse(
            success=True,
            data=CaseResponseData(
                case_id=case.id,
                audit_id=audit_id,
                status="needs_manual_review",
                reasoning_trace=None,
                red_flags=[],
                latency_ms=latency_ms
            )
        )
        
    # 3. Successful Classification
    db.add(AuditLog(
        audit_id=audit_id, 
        event="classify_success",
        response_payload=llm_result.model_dump_json()
    ))
    
    # 2.5 Generate Embedding
    embedding = get_embedding(safe_text)
    embedding_str = json.dumps(embedding) if embedding else None

    # 3. Create Case
    case = Case(
        audit_id=audit_id,
        raw_text_deidentified=safe_text,
        pii_token_map=token_map,
        fraud_type=llm_result.fraud_type,
        risk_score=llm_result.risk_score,
        confidence=llm_result.confidence,
        verdict=llm_result.verdict,
        reporting_portal=llm_result.reporting_portal,
        reasoning_trace=llm_result.reasoning_trace,
        status="classified",
        embedding=embedding_str
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    # Add Red Flags
    red_flag_schemas = []
    for flag in llm_result.red_flags:
        rf = CaseRedFlag(
            case_id=case.id,
            flag_id=flag.flag_id,
            category=flag.category,
            evidence=flag.evidence,
            explanation=flag.explanation,
            confidence_score=flag.confidence_score,
            mha_ncrb_citation=flag.mha_ncrb_citation
        )
        db.add(rf)
        red_flag_schemas.append(RedFlagSchema(
            flag_id=flag.flag_id,
            category=flag.category,
            evidence=flag.evidence,
            explanation=flag.explanation,
            confidence_score=flag.confidence_score,
            mha_ncrb_citation=flag.mha_ncrb_citation
        ))
        
    # Extract Infrastructure dynamically from the PII token map
    try:
        tokens = json.loads(token_map)
        for token, value in tokens.items():
            val_hash = hashlib.sha256(value.encode()).hexdigest()
            node = db.query(InfraNode).filter(InfraNode.value_hash == val_hash).first()
            if not node:
                node = InfraNode(type="extracted_pii", value_hash=val_hash)
                db.add(node)
                db.commit()
                db.refresh(node)
            
            # Link case to infra
            link = CaseInfraLink(case_id=case.id, infra_node_id=node.id)
            db.merge(link)
    except Exception:
        pass
        
    db.commit()
    
    # Trigger clustering algorithms automatically!
    recluster_campaigns(db)
    
    return ClassifyResponse(
        success=True,
        data=CaseResponseData(
            case_id=case.id,
            audit_id=audit_id,
            fraud_type=case.fraud_type,
            risk_score=case.risk_score,
            confidence=case.confidence,
            verdict=case.verdict,
            reporting_portal=case.reporting_portal,
            reasoning_trace=case.reasoning_trace,
            status=case.status,
            latency_ms=latency_ms,
            red_flags=red_flag_schemas
        )
    )

@router.get("/cases/{case_id}", response_model=ClassifyResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
         return ClassifyResponse(success=False, error="Case not found")
         
    rfs = [RedFlagSchema(
        flag_id=rf.flag_id,
        category=rf.category,
        evidence=rf.evidence,
        explanation=rf.explanation,
        confidence_score=rf.confidence_score,
        mha_ncrb_citation=rf.mha_ncrb_citation
    ) for rf in case.red_flags]
    
    return ClassifyResponse(
        success=True,
        data=CaseResponseData(
            case_id=case.id,
            audit_id=case.audit_id,
            fraud_type=case.fraud_type,
            risk_score=case.risk_score,
            confidence=case.confidence,
            verdict=case.verdict,
            reporting_portal=case.reporting_portal,
            reasoning_trace=case.reasoning_trace,
            status=case.status,
            red_flags=rfs
        )
    )

@router.get("/cases")
def get_all_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).all()
    result = []
    for case in cases:
        result.append({
            "id": case.id,
            "audit_id": case.audit_id,
            "fraud_type": case.fraud_type,
            "risk_score": case.risk_score,
            "confidence": case.confidence,
            "verdict": case.verdict,
            "district": case.district,
            "campaign_id": case.campaign_id,
            "status": case.status,
            "created_at": case.created_at,
            "raw_text_deidentified": case.raw_text_deidentified,
            "reporting_portal": case.reporting_portal,
        })
    return {"success": True, "data": result}

from pydantic import BaseModel
class FeedbackRequest(BaseModel):
    case_id: int
    verdict: str

@router.post("/feedback")
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.status = request.verdict
    db.commit()
    return {"success": True, "data": {"caseId": case.id, "status": case.status}}

@router.get("/audit/{audit_id}")
def get_audit(audit_id: str, db: Session = Depends(get_db)):
    """Simple viewable audit log requirement C.6"""
    logs = db.query(AuditLog).filter(AuditLog.audit_id == audit_id).order_by(AuditLog.created_at).all()
    if not logs:
        raise HTTPException(status_code=404, detail="Audit ID not found")
    
    return {
        "success": True,
        "data": [{
            "event": log.event,
            "created_at": log.created_at,
            "request": log.request_payload,
            "response": log.response_payload
        } for log in logs]
    }
