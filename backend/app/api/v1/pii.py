"""PII Vault endpoints (F12)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, constr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser, require_min_role
from app.core.errors import ValidationError, ok
from app.services import pii_service
from app.services.audit_service import log_pii_access

router = APIRouter(prefix="/pii", tags=["pii"])


class DecryptRequest(BaseModel):
    token: str
    justification: constr(min_length=5)  # type: ignore[valid-type]


@router.post("/decrypt", dependencies=[Depends(require_min_role("officer"))])
async def decrypt_pii(
    req: DecryptRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Decrypt a PII token to plaintext.
    Requires 'officer' or 'admin' role. Mandatory justification logged to audit chain.
    """
    master_key = settings.PII_MASTER_KEY.encode("utf-8")

    plaintext = await pii_service.decrypt_token(req.token, db, master_key)
    if not plaintext:
        # Avoid telling the user whether the token exists or decryption failed
        raise ValidationError("Invalid token or decryption failed")

    # Log to tamper-evident audit chain
    await log_pii_access(
        case_id=None,  # In a real scenario we might require case_id in the request too
        actor_id=user.id,
        justification=req.justification,
        db=db,
    )

    return ok({"original": plaintext})
