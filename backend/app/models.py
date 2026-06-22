from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String)
    case_count = Column(Integer, default=0)
    total_estimated_loss = Column(Integer, default=0)
    last_clustered_at = Column(DateTime)
    
    cases = relationship("Case", back_populates="campaign")

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String, unique=True, index=True, nullable=False)
    raw_text_deidentified = Column(Text, nullable=False)
    pii_token_map = Column(Text)
    fraud_type = Column(String)
    risk_score = Column(Integer)
    confidence = Column(Float)
    verdict = Column(String)
    reporting_portal = Column(String)
    district = Column(String, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    status = Column(String, default="classified", nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    campaign = relationship("Campaign", back_populates="cases")
    red_flags = relationship("CaseRedFlag", back_populates="case")
    infra_links = relationship("CaseInfraLink", back_populates="case")

class CaseRedFlag(Base):
    __tablename__ = "case_red_flags"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    flag_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    evidence = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    
    case = relationship("Case", back_populates="red_flags")

class InfraNode(Base):
    __tablename__ = "infra_nodes"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    value_hash = Column(String, unique=True, index=True, nullable=False)
    
    infra_links = relationship("CaseInfraLink", back_populates="infra_node")

class CaseInfraLink(Base):
    __tablename__ = "case_infra_links"
    case_id = Column(Integer, ForeignKey("cases.id"), primary_key=True)
    infra_node_id = Column(Integer, ForeignKey("infra_nodes.id"), primary_key=True, index=True)
    
    case = relationship("Case", back_populates="infra_links")
    infra_node = relationship("InfraNode", back_populates="infra_links")

class District(Base):
    __tablename__ = "districts"
    name = Column(String, primary_key=True, index=True)
    state = Column(String)
    geojson_id = Column(String)
    
    weekly_stats = relationship("DistrictWeeklyStat", back_populates="district_ref")

class DistrictWeeklyStat(Base):
    __tablename__ = "district_weekly_stats"
    id = Column(Integer, primary_key=True, index=True)
    district_name = Column(String, ForeignKey("districts.name"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    complaint_count = Column(Integer, nullable=False)
    prior_week_complaint_count = Column(Integer, default=1)
    estimated_loss = Column(Integer, nullable=False)
    priority_score = Column(Float)
    
    district_ref = relationship("District", back_populates="weekly_stats")

class CaseFeedback(Base):
    __tablename__ = "case_feedback"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    marked_by = Column(String)
    verdict = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String, nullable=False)
    event = Column(String, nullable=False)
    request_payload = Column(Text)
    response_payload = Column(Text)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=func.now(), nullable=False)
