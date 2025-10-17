from typing import Any, Generic, TypeVar

from pydantic import BaseModel

_T = TypeVar("_T", bound=list | dict[str, Any])


class GenericResponse(BaseModel, Generic[_T]):
    success: bool
    """请求是否成功处理"""
    code: int = 200
    """	HTTP 状态码，通常为 200"""
    data: _T | None = None
    """响应数据"""
    message: str | None = None
    """请求失败理由"""
