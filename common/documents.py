import json
from hashlib import sha256
from typing import Annotated, List, Dict, Any
from pydantic import UUID4, BaseModel, Field, PositiveInt, NonNegativeInt, HttpUrl
from pydantic import AfterValidator, PlainSerializer
from annotated_types import Ge, Le
from datetime import datetime
from uuid import uuid4
from enum import StrEnum

HexUUID4 = Annotated[UUID4, PlainSerializer(lambda x: x.hex, return_type=str)]
HTTPURLStr = Annotated[str, AfterValidator(lambda x: str(HttpUrl(x)))]

Priority = Annotated[NonNegativeInt, Ge(0), Le(100)]


class WebsiteState(StrEnum):
    # 测试
    Testing = 'testing'
    # 正常
    Active = 'active'
    # 停用
    Paused = 'paused'


class SpiderTaskStatus(StrEnum):
    Pending = 'pending'
    Running = 'running'
    Completed = 'completed'
    Failed = 'failed'
    Cancelled = 'cancelled'


class Spider(BaseModel):
    version: NonNegativeInt = 0
    spider_id: str = ''
    name: str = ''
    args: list = []
    kwargs: dict = {}


class Website(BaseModel):
    version: NonNegativeInt = 0
    site_id: str = ''
    name: str = ''
    base_url: HTTPURLStr = ''
    description: str = ''
    state: WebsiteState = WebsiteState.Testing
    spider_id: str = ''
    last_crawled_at: datetime = Field(default_factory=datetime.now)


class SpiderTask(BaseModel):
    version: NonNegativeInt = 0
    task_id: HexUUID4 = Field(default_factory=uuid4)
    spider_id: str = ''
    site_id: str = ''
    urls: List[HTTPURLStr] = []
    status: SpiderTaskStatus = SpiderTaskStatus.Pending
    created_at: datetime = Field(default_factory=datetime.now)
    launched_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(default_factory=datetime.now)
    priority: Priority = 1
    jiasai: bool = False
    start_from_page: NonNegativeInt = 0
    max_pages: PositiveInt = 0
    max_items: PositiveInt = 0
    total_pages: NonNegativeInt = 0
    total_items: NonNegativeInt = 0
    data: dict = {}
    digest_v: NonNegativeInt = 0


class SpiderItem(BaseModel):
    version: NonNegativeInt = 0
    item_id: HexUUID4 = Field(default_factory=uuid4)
    task_id: HexUUID4 = ''
    crawled_at: datetime = Field(default_factory=datetime.now)
    page: NonNegativeInt = 0
    meta_data: dict = {}
    data: dict = {}
    digest_v: NonNegativeInt = 0
    digest: str = ''


def data_digest_fn(data: Dict[str, Any], version: int = 0):
    if version == 0:
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        data_hash = sha256(data_str.encode(encoding='utf-8')).hexdigest()
        data_digest = data_hash.hexdigest()[:16]
        return data_digest
    else:
        raise ValueError(f"Unknown data digest generator version: {version}")
