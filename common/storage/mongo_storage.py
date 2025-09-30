import json
import logging
import traceback

from enum import StrEnum
from typing import Union, Optional, Dict, List
from pymongo import MongoClient
from pymongo import (
    InsertOne,
    UpdateOne,
    UpdateMany,
    ReplaceOne,
    DeleteOne,
    DeleteMany,
)
from pymongo.results import (
    InsertOneResult,
    InsertManyResult,
    DeleteResult,
    UpdateResult,
)

class DatabaseType(StrEnum):
    TEST = 'test'
    PROD = 'prod'
    DEV = 'dev'

# TODO: 支持 json lines https://jsonlines.org

# collections:
# Sites: 爬虫站点信息, id=site_id
# Tasks: 爬虫任务信息, id=task_id
# Items: 爬虫任务数据, id=task_id


class DBClient:
    def __init__(self, db_type: str, host: str = 'localhost', port: int = 27017) -> None:
        self.logger = logging.getLogger(__name__)

        self.db_type = db_type
        try:
            uri = f"mongodb://{host}:{port}"
            self.client = MongoClient(uri)
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.client.close()

    def _ensure_valid_documents(self, documents: Union[Dict, List[Dict]]) -> List[Dict]:
        if isinstance(documents, dict):
            if len(documents) == 0:
                raise ValueError(f"Empty document")
            return [ documents ]

        elif isinstance(documents, list):
            if len(documents) == 0:
                raise ValueError(f"Empty documents")

            for doc in documents:
                if not isinstance(doc, dict):
                    raise TypeError(f"Invalid document type: {type(doc)}")
                if len(documents) == 0:
                    raise ValueError(f"Empty document")
            return documents

        else:
            raise TypeError(f"Invalid documents type: {type(documents)}")

    # https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/crud/insert
    def insert(self, collection_name: str, documents: Union[Dict, List[Dict]]):
        try:
            database = self.client[self.db_type]
            collection = database[collection_name]
            documents = self._ensure_valid_documents(documents)
            if len(documents) == 1:
                document = documents[0]
                result = collection.insert_one(document)
                return InsertManyResult(inserted_ids=[result.inserted_id], acknowledged=result.acknowledged)
            else:
                return collection.insert_many(documents)

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Failed to insert documents into {collection_name}: {e}")
            return InsertManyResult(inserted_ids=[], acknowledged=False)

    # https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/crud/delete
    def delete(self, collection_name: str, query_filter: dict):
        try:
            database = self.client[self.db_type]
            collection = database[collection_name]
            collection.delete_many(filter=query_filter)

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Failed to delete documents")
            return

    # https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/crud/query
    def find(self, collection_name: str, query_filter: dict, projection: list[str], limit=None, skip=None):
        try:
            database = self.client[self.db_type]
            collection = database[collection_name]
            return collection.find(filter=query_filter,
                                   projection=projection,
                                   limit=0 if limit is None else int(limit),
                                   skip=0 if skip is None else int(skip),
                                   comment=f"Finding documents with filter: {query_filter}, projection: {projection}, limit: {limit}")

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Failed to find with filter {query_filter}: {e}")
            return []

    # https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/crud/update
    def update(self, collection_name: str, query_filter: dict, operation: dict):
        try:
            database = self.client[self.db_type]
            collection = database[collection_name]
            result = collection.update_many(filter=query_filter,
                                            update=operation,
                                            comment=f"Updating documents with filter: {query_filter}, operation: {operation}")
            return result

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Failed to update documents filter: {query_filter}, operation: {operation}: {e}")
            return

    # https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/aggregation
    def aggregate(self):
        pass

    # https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/crud/query/count/#std-label-pymongo-accurate-count
    def count(self, collection_name: str, query_filter: dict = {}):
        try:
            database = self.client[self.db_type]
            collection = database[collection_name]
            cnt = collection.count_documents(filter=query_filter, comment="Counting documents")
            return cnt

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Failed to count documents with filter {query_filter}: {e}")
            return 0

    # https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/crud/query/count/#std-label-pymongo-estimated-count
    def estimated_count(self, collection_name: str):
        try:
            database = self.client[self.db_type]
            collection = database[collection_name]
            cnt = collection.estimated_document_count(comment="Estimatedly counting documents")
            return cnt

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Failed to estimatedly count documents: {e}")
            return 0

    # https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/crud/query/distinct/#std-label-pymongo-distinct
    def distinct(self, collection_name: str, field_name: str, query_filter: Optional[dict] = None):
        try:
            database = self.client[self.db_type]
            collection = database[collection_name]
            values = collection.distinct(key=field_name,
                                         filter=query_filter,
                                         comment=f"Fetching distinct values for field '{field}' in collection '{collection_name}' with filter '{query_filter}'")
            return values

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Failed to distinct documents: {e}")
            return []


__all__ = [
    'DatabaseType',
    'DBClient',
]
