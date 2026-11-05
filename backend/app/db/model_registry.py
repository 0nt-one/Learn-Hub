"""
导入九个模型，使这九张表登记进去
"""


import app.models.category
import app.models.course
import app.models.favorite
import app.models.learning_record
import app.models.notification
import app.models.operation_log
import app.models.resource
import app.models.review_record
import app.models.user


EXPECTED_TABLES = frozenset(
    {
        "users",
        "courses",
        "categories",
        "resources",
        "review_records",
        "learning_records",
        "favorites",
        "notifications",
        "operation_logs",
    }
)
