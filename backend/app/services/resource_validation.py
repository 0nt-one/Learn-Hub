from collections.abc import Callable


def validate_video_metadata(
    duration_seconds: int | None,
    page_count: int | None,
) -> None:
    if duration_seconds is None or duration_seconds <= 0:
        raise ValueError("视频必须填写正数时长")
    if page_count is not None:
        raise ValueError("视频不能填写页数")


def validate_document_metadata(
    duration_seconds: int | None,
    page_count: int | None,
) -> None:
    if duration_seconds is not None:
        raise ValueError("文档不能填写视频时长")
    if page_count is not None and page_count <= 0:
        raise ValueError("文档页数必须是正数")


def validate_link_metadata(
    duration_seconds: int | None,
    page_count: int | None,
) -> None:
    if duration_seconds is not None or page_count is not None:
        raise ValueError("链接不能填写时长或页数")


ResourceValidator = Callable[[int | None, int | None], None]

_VALIDATORS: dict[str, ResourceValidator] = {
    "document": validate_document_metadata,
    "video": validate_video_metadata,
    "link": validate_link_metadata,
}


def validator_for(resource_type: str) -> ResourceValidator:
    try:
        return _VALIDATORS[resource_type]
    except KeyError as exc:
        raise ValueError("未知的资源类型") from exc

