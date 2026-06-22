# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class RedFlagSchema(BaseModel):
    flag_id: str
    category: str
    evidence: str
    explanation: str
    confidence_score: Optional[int] = None
    mha_ncrb_citation: Optional[str] = None

class CaseResponseData(BaseModel):
    case_id: int
    audit_id: str
    fraud_type: Optional[str]
    risk_score: Optional[int]
    confidence: Optional[float]
    verdict: Optional[str]
    reporting_portal: Optional[str]
    reasoning_trace: Optional[str] = None
    status: str
    latency_ms: Optional[int] = None
    red_flags: List[RedFlagSchema] = []

class BaseResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None

class ClassifyRequest(BaseModel):
    raw_text: str

class ClassifyResponse(BaseResponse):
    data: Optional[CaseResponseData] = None

class NodeSchema(BaseModel):
    id: str
    label: str
    group: str
    degree: int
    fraud_type: Optional[str] = None

class LinkSchema(BaseModel):
    source: str
    target: str
    type: str

class CampaignSchema(BaseModel):
    id: int
    label: str
    case_count: int
    total_estimated_loss: int
    cross_jurisdiction: Optional[bool] = False
    primary_target_infra_id: Optional[int] = None
    primary_target_betweenness: Optional[float] = None
    pct_connectivity_lost: Optional[float] = None
    fractures_network: Optional[bool] = False

class GraphData(BaseModel):
    nodes: List[NodeSchema]
    links: List[LinkSchema]
    campaigns: List[CampaignSchema]

class GraphResponse(BaseResponse):
    data: Optional[GraphData] = None

class DistrictStatSchema(BaseModel):
    name: str
    state: Optional[str] = None
    priority_score: float
    complaint_count: int
    estimated_loss: int
    active_campaigns: int
    trend: str

class DistrictStatsResponse(BaseResponse):
    data: Optional[List[DistrictStatSchema]] = None

class DistrictSummaryData(DistrictStatSchema):
    state: str
    top_fraud_types: List[str]

class DistrictSummaryResponse(BaseResponse):
    data: Optional[DistrictSummaryData] = None
