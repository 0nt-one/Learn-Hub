from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.operation_log import OperationLog
from app.models.resource import Resource


@dataclass(frozen=True)
class ResourceReviewed:
    review_id: int
    resource_id: int
    owner_id: int
    reviewer_id: int
    decision: str
    request_id: str


ReviewHandler = Callable[[Session, ResourceReviewed], None]


class ReviewEventDispatcher:
    def __init__(self, handlers: tuple[ReviewHandler, ...]) -> None:
        self.handlers = handlers

    def publish(self, session: Session, event: ResourceReviewed) -> None:
        for handler in self.handlers:
            handler(session, event)


def add_review_notification(session: Session, event: ResourceReviewed) -> None:
    approved = event.decision == "approved"
    # 通知是事件快照：标题直接写进文案，之后资源改名不影响历史通知
    resource = session.get(Resource, event.resource_id)
    resource_title = resource.title if resource is not None else "资源"
    session.add(
        Notification(
            user_id=event.owner_id,
            review_record_id=event.review_id,
            kind="review_result",
            title="资源审核通过" if approved else "资源审核未通过",
            content=(
                f"你的资源《{resource_title}》已通过审核。"
                if approved
                else f"你的资源《{resource_title}》未通过审核，请查看审核意见。"
            ),
        )
    )


def add_review_audit(session: Session, event: ResourceReviewed) -> None:
    session.add(
        OperationLog(
            actor_id=event.reviewer_id,
            action="resource.review",
            target_type="resource",
            target_id=event.resource_id,
            request_id=event.request_id,
            summary="审核通过资源" if event.decision == "approved" else "拒绝资源审核",
        )
    )
