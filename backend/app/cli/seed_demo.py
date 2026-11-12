"""
demo数据库生成脚本
"""

from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR, Settings
from app.core.passwords import hash_password
from app.db.engine import create_db_engine
from app.db.init_db import initialize_database
from app.models.user import User
from app.schemas.category import CategoryCreateRequest
from app.schemas.course import CourseCreateRequest
from app.schemas.resource import ResourceCreateRequest
from app.schemas.review import ReviewCreateRequest
from app.services.categories import create_category
from app.services.courses import create_course
from app.services.favorites import add_favorite
from app.services.learning import upsert_learning_record
from app.services.resources import create_resource, submit_resource
from app.services.review_events import (
    ReviewEventDispatcher,
    add_review_audit,
    add_review_notification,
)
from app.services.reviews import review_resource


DEMO_DATABASE = BACKEND_DIR / "data" / "learn_hub_demo.db"
DEMO_PASSWORD = "LearnHubDemo2026!"
USERS = (
    ("demo_admin", "林知远", "admin"),
    ("demo_chen", "陈老师", "teacher"),
    ("demo_wang", "王老师", "teacher"),
    ("demo_zhou", "周同学", "student"),
    ("demo_li", "李同学", "student"),
    ("demo_sun", "孙同学", "student"),
)
COURSES = (
    ("PY-101", "Python 编程入门", "从变量、函数到文件处理，逐步建立编程思维。", "demo_chen"),
    ("WEB-201", "现代 Web 开发", "用真实页面练习 HTML、CSS、TypeScript 与组件开发。", "demo_wang"),
    ("DB-210", "数据库原理与应用", "理解关系模型、SQL 查询、索引与数据设计。", "demo_chen"),
    ("DS-301", "数据结构与算法", "以可视化和练习题掌握常见数据结构。", "demo_wang"),
    ("API-220", "后端接口设计", "从 HTTP 到接口契约、权限和服务分层。", "demo_chen"),
)
CATEGORIES = (
    ("课程讲义", "课堂知识点与章节速查资料"),
    ("实践项目", "可跟着动手完成的项目练习"),
    ("视频课程", "适合分段学习的视频内容"),
    ("工具文档", "框架、语言与工具的参考文档"),
    ("习题解析", "典型题目、解题思路与复盘"),
)
# 类型、标题、简介、课程、分类、投稿人、审核状态、额外信息。
# URL 使用 example.org 的演示占位地址；不会假装提供真实文件或视频。
RESOURCES = (
    ("document", "Python 基础语法一页通", "变量、条件分支和循环的关键知识点，适合课前预习。", "PY-101", "课程讲义", "demo_chen", "approved", 12),
    ("video", "用一个记账本学会 Python 函数", "从需求拆解到函数封装，跟着示例完成第一版记账本。", "PY-101", "视频课程", "demo_chen", "approved", 1680),
    ("link", "Python 官方教程学习路线", "按章节整理阅读顺序，附课堂练习建议。", "PY-101", "工具文档", "demo_zhou", "approved", None),
    ("document", "CSS 布局实战笔记", "用 Flexbox 和 Grid 完成响应式课程主页。", "WEB-201", "课程讲义", "demo_wang", "approved", 24),
    ("video", "Vue 组件通信：从零搭建任务面板", "通过 props、事件和组合式 API 实现完整交互。", "WEB-201", "视频课程", "demo_wang", "approved", 2520),
    ("link", "TypeScript 常用类型速查", "整理前端项目最常用的类型声明与易错点。", "WEB-201", "工具文档", "demo_li", "approved", None),
    ("document", "SQL 查询练习与答案", "覆盖连接、分组、子查询和排序的课堂练习。", "DB-210", "习题解析", "demo_chen", "approved", 32),
    ("video", "索引为什么能加快查询", "从 B 树结构到执行计划，建立直观理解。", "DB-210", "视频课程", "demo_chen", "approved", 1380),
    ("document", "二叉树遍历图解", "前序、中序、后序遍历的步骤与代码示意。", "DS-301", "课程讲义", "demo_wang", "approved", 18),
    ("link", "FastAPI 接口设计清单", "从请求校验到错误响应的实用检查清单。", "API-220", "工具文档", "demo_chen", "approved", None),
    ("document", "从零设计一个课程资源库", "学生作品：需求拆解、数据表和页面结构。", "API-220", "实践项目", "demo_zhou", "pending", 20),
    ("video", "排序算法可视化演示", "学生投稿：比较冒泡、插入和快速排序的过程。", "DS-301", "视频课程", "demo_sun", "pending", 1140),
    ("document", "前端表单校验案例", "教师备课草稿：登录表单的交互与错误提示。", "WEB-201", "实践项目", "demo_wang", "draft", 16),
    ("link", "数据库课程链接汇总", "待补充可访问的资料地址与章节说明。", "DB-210", "工具文档", "demo_li", "rejected", None),
)


def seed_demo_database(database_path: Path = DEMO_DATABASE) -> str:
    """Seed only a fresh database; repeated calls leave its contents unchanged."""
    database_path = database_path.resolve()
    if database_path == (BACKEND_DIR / "data" / "learn_hub.db").resolve():
        raise ValueError("演示数据不能写入默认业务数据库")
    if database_path.exists():
        raise FileExistsError(f"数据库已存在，不会覆盖：{database_path}")

    settings = Settings(database_url=f"sqlite:///{database_path.as_posix()}")
    initialize_database(settings)
    engine = create_db_engine(settings)
    try:
        with Session(engine) as session:
            if session.scalar(select(User.id).limit(1)) is not None:
                raise RuntimeError("演示数据库必须为空")

            users = {}
            for username, display_name, role in USERS:
                user = User(
                    username=username,
                    display_name=display_name,
                    role=role,
                    password_hash=hash_password(DEMO_PASSWORD),
                )
                session.add(user)
                users[username] = user
            session.commit()

            admin = users["demo_admin"]
            categories = {}
            for name, description in CATEGORIES:
                categories[name] = create_category(
                    session,
                    actor=admin,
                    data=CategoryCreateRequest(name=name, description=description),
                    request_id=str(uuid4()),
                )

            courses = {}
            teacher_by_course = {}
            for code, title, description, teacher_username in COURSES:
                teacher_by_course[code] = teacher_username
                courses[code] = create_course(
                    session,
                    actor=admin,
                    data=CourseCreateRequest(
                        code=code,
                        title=title,
                        description=description,
                        teacher_id=users[teacher_username].id,
                    ),
                    request_id=str(uuid4()),
                )

            dispatcher = ReviewEventDispatcher((add_review_notification, add_review_audit))
            resources = []
            for index, (kind, title, description, course_code, category_name, owner_name, status, extent) in enumerate(RESOURCES, start=1):
                resource = create_resource(
                    session,
                    actor=users[owner_name],
                    data=ResourceCreateRequest(
                        title=title,
                        description=description,
                        resource_type=kind,
                        url=f"https://example.org/learn-hub/demo/resource-{index}",
                        duration_seconds=extent if kind == "video" else None,
                        page_count=extent if kind == "document" else None,
                        course_id=courses[course_code].id,
                        category_id=categories[category_name].id,
                    ),
                    request_id=str(uuid4()),
                )
                if status != "draft":
                    resource = submit_resource(
                        session,
                        actor=users[owner_name],
                        resource_id=resource.id,
                        expected_version=resource.version_id,
                        request_id=str(uuid4()),
                    )
                if status in {"approved", "rejected"}:
                    reviewer = (
                        admin
                        if owner_name == teacher_by_course[course_code]
                        else users[teacher_by_course[course_code]]
                    )
                    _, resource = review_resource(
                        session,
                        actor=reviewer,
                        resource_id=resource.id,
                        data=ReviewCreateRequest(
                            expected_version=resource.version_id,
                            decision=status,
                            comment=(
                                "内容清晰，适合加入课程资源库。"
                                if status == "approved"
                                else "链接尚未补全，请补充可访问的资料后重新提交。"
                            ),
                        ),
                        request_id=str(uuid4()),
                        dispatcher=dispatcher,
                    )
                resources.append(resource)

            for username, resource_indexes in (
                ("demo_zhou", (0, 1, 3, 6, 9)),
                ("demo_li", (0, 4, 5, 8)),
                ("demo_sun", (1, 2, 7)),
            ):
                for resource_index in resource_indexes:
                    add_favorite(session, user_id=users[username].id, resource_id=resources[resource_index].id)
            for username, progress_by_index in (
                ("demo_zhou", ((0, 100), (1, 65), (3, 32), (6, 80))),
                ("demo_li", ((4, 45), (5, 100), (8, 20))),
                ("demo_sun", ((1, 30), (2, 75), (7, 10))),
            ):
                for resource_index, progress in progress_by_index:
                    upsert_learning_record(
                        session,
                        user_id=users[username].id,
                        resource_id=resources[resource_index].id,
                        progress=progress,
                    )
    finally:
        engine.dispose()
    return f"演示数据库已创建：{database_path}（{len(USERS)} 位用户、{len(COURSES)} 门课程、{len(RESOURCES)} 条资源）"


def main() -> int:
    try:
        print(seed_demo_database())
    except (FileExistsError, ValueError, RuntimeError) as exc:
        print(exc)
        return 1
    print("演示账号见 backend/README.md；所有账号使用同一演示密码。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
