"""学习进度：每次上报都是"最后成功写入值"，不做多端版本合并。"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.db.time import utc_now
from app.models.category import Category
from app.models.course import Course
from app.models.learning_record import LearningRecord
from app.models.resource import Resource
from app.services.resources import get_public_resource


@dataclass(frozen=True)
class LearningResourceContext:
    """列表里每条记录对应的资源上下文。

    is_available 的判定与 services.resources.get_public_resource 一致，
    两边必须同步改，否则会出现"详情能打开但进度里显示已下架"。
    """

    resource: Resource
    course_title: str
    category_name: str
    is_available: bool


def upsert_learning_record(
    session: Session,
    *,
    user_id: int,
    resource_id: int,
    progress: int,
) -> LearningRecord:
    """不存在则创建，存在则覆盖 progress 并刷新 last_accessed_at。

    用 SQLite 的 ON CONFLICT DO UPDATE 做安全 upsert：并发首次写入不会各插一条，
    也不需要靠捕获 IntegrityError 再猜是哪条唯一键冲突（契约 L168 的要求）。
    """

    # 只有常规可见的资源才能记录进度，否则等于给不可见资源留痕
    get_public_resource(session, resource_id)

    now = utc_now()
    try:
        session.execute(
            insert(LearningRecord)
            .values(
                user_id=user_id,
                resource_id=resource_id,
                progress=progress,
                last_accessed_at=now,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=[LearningRecord.user_id, LearningRecord.resource_id],
                # Core 语句不会触发模型的 onupdate，这里必须显式写
                set_={
                    "progress": progress,
                    "last_accessed_at": now,
                    "updated_at": now,
                },
            )
        )
        record = session.scalar(
            select(LearningRecord).where(
                LearningRecord.user_id == user_id,
                LearningRecord.resource_id == resource_id,
            )
        )
        assert record is not None
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(record)
    return record


def list_my_learning_records(
    session: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[LearningRecord], dict[int, LearningResourceContext], int]:
    statement = select(LearningRecord).where(LearningRecord.user_id == user_id)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    records = list(
        session.scalars(
            statement.order_by(
                LearningRecord.last_accessed_at.desc(), LearningRecord.id.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )

    ids = {record.resource_id for record in records}
    contexts: dict[int, LearningResourceContext] = {}
    if ids:
        # 这里**不加**可见性过滤：资源下架后仍要能显示标题与课程名。
        # 是否返回 url 由 is_available 决定，在 schema 层控制。
        rows = session.execute(
            select(
                Resource,
                Course.title,
                Category.name,
                Course.is_active,
                Category.is_active,
            )
            .join(Course, Course.id == Resource.course_id)
            .join(Category, Category.id == Resource.category_id)
            .where(Resource.id.in_(ids))
        ).all()
        for resource, course_title, category_name, course_active, category_active in rows:
            contexts[resource.id] = LearningResourceContext(
                resource=resource,
                course_title=course_title,
                category_name=category_name,
                is_available=(
                    resource.status == "approved"
                    and bool(course_active)
                    and bool(category_active)
                ),
            )
    return records, contexts, total
