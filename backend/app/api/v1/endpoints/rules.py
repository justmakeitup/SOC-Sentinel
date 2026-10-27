"""Detection rules management and telemetry evaluation endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.engine.correlator import default_engine
from app.engine.schemas import (
    DetectionRuleDetailResponse,
    DetectionRuleUpdateRequest,
    ReplayRequest,
    ReplayResponse,
)
from app.models.event import NormalizedSecurityEvent
from app.models.rule import DetectionRule
from app.models.user import User, UserRole
from app.schemas.alert import SecurityAlertRead

router = APIRouter(prefix="/rules", tags=["Detection Rules"])


def _to_detail_response(rule: DetectionRule) -> DetectionRuleDetailResponse:
    logic = rule.rule_logic or {}
    plugin = default_engine.registry.get(rule.rule_code)
    assumptions = (
        plugin.assumptions
        if plugin
        else logic.get("assumptions", [])
    )
    limitations = (
        plugin.limitations
        if plugin
        else logic.get("limitations", [])
    )
    expected_fps = (
        plugin.expected_false_positives
        if plugin
        else logic.get("expected_false_positives", [])
    )

    return DetectionRuleDetailResponse(
        id=rule.id,
        rule_code=rule.rule_code,
        name=rule.name,
        description=rule.description,
        severity=rule.severity,
        rule_type=rule.rule_type,
        is_active=rule.is_active,
        time_window_seconds=rule.time_window_seconds,
        threshold_count=rule.threshold_count,
        mitre_tactic=rule.mitre_tactic,
        mitre_technique=rule.mitre_technique,
        remediation_guidance=rule.remediation_guidance,
        assumptions=assumptions,
        limitations=limitations,
        expected_false_positives=expected_fps,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.get(
    "",
    response_model=List[DetectionRuleDetailResponse],
    summary="List all detection rules with operational guidance and ATT&CK mapping",
)
def list_detection_rules(
    db: Session = Depends(get_db),
    active_only: bool = Query(default=False),
) -> List[DetectionRuleDetailResponse]:
    """Returns catalog of transparent rule-based detection rules."""
    default_engine.sync_rules(db)
    query = db.query(DetectionRule)
    if active_only:
        query = query.filter(DetectionRule.is_active.is_(True))

    rules = query.order_by(DetectionRule.rule_code.asc()).all()
    return [_to_detail_response(r) for r in rules]


@router.get(
    "/{rule_identifier}",
    response_model=DetectionRuleDetailResponse,
    summary="Get detection rule details by code or UUID",
)
def get_detection_rule(
    rule_identifier: str,
    db: Session = Depends(get_db),
) -> DetectionRuleDetailResponse:
    """Retrieves specific detection rule by mnemonic code (e.g. SEC-AUTH-001) or UUID."""
    default_engine.sync_rules(db)

    rule = None
    try:
        val_uuid = UUID(rule_identifier)
        rule = db.query(DetectionRule).filter(DetectionRule.id == val_uuid).first()
    except (ValueError, AttributeError):
        pass

    if not rule:
        rule = (
            db.query(DetectionRule)
            .filter(DetectionRule.rule_code == rule_identifier.upper())
            .first()
        )

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection rule '{rule_identifier}' not found.",
        )

    return _to_detail_response(rule)


@router.patch(
    "/{rule_identifier}",
    response_model=DetectionRuleDetailResponse,
    summary="Update detection rule threshold, window, severity, or active state",
)
def update_detection_rule(
    rule_identifier: str,
    update_data: DetectionRuleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([
            UserRole.DETECTION_ENGINEER,
            UserRole.SOC_MANAGER,
            UserRole.ADMIN,
        ])
    ),
) -> DetectionRuleDetailResponse:
    """Updates tunable thresholds or toggles rule activation."""
    default_engine.sync_rules(db)

    rule = None
    try:
        val_uuid = UUID(rule_identifier)
        rule = db.query(DetectionRule).filter(DetectionRule.id == val_uuid).first()
    except (ValueError, AttributeError):
        pass

    if not rule:
        rule = (
            db.query(DetectionRule)
            .filter(DetectionRule.rule_code == rule_identifier.upper())
            .first()
        )

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection rule '{rule_identifier}' not found.",
        )

    if update_data.is_active is not None:
        rule.is_active = update_data.is_active
    if update_data.threshold_count is not None:
        rule.threshold_count = update_data.threshold_count
    if update_data.time_window_seconds is not None:
        rule.time_window_seconds = update_data.time_window_seconds
    if update_data.severity is not None:
        rule.severity = update_data.severity

    rule.version += 1
    db.commit()
    db.refresh(rule)

    return _to_detail_response(rule)


@router.post(
    "/evaluate",
    response_model=List[SecurityAlertRead],
    summary="Trigger detection engine evaluation over recent security events",
)
def evaluate_recent_events(
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> List[SecurityAlertRead]:
    """Evaluates the latest ingested events against all active detection rules."""
    events = (
        db.query(NormalizedSecurityEvent)
        .order_by(NormalizedSecurityEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
    # Chronological order for sequence correlation
    events.reverse()

    alerts = default_engine.evaluate_events(events, db)
    return [SecurityAlertRead.model_validate(a) for a in alerts]


@router.post(
    "/replay",
    response_model=ReplayResponse,
    summary="Replay historical or synthetic events within a timestamp window",
)
def replay_events(
    request: ReplayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([
            UserRole.DETECTION_ENGINEER,
            UserRole.SOC_MANAGER,
            UserRole.ADMIN,
        ])
    ),
) -> ReplayResponse:
    """Replays events within specified time range to reproduce findings and verify rule tuning."""
    if request.end_time <= request.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be strictly after start_time.",
        )

    result = default_engine.replay_time_window(
        start_time=request.start_time,
        end_time=request.end_time,
        db=db,
    )
    return ReplayResponse(**result)
