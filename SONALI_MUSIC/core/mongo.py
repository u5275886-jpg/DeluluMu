import os
import json
import asyncio
import copy
import uuid
from ..logging import LOGGER

LOGGER(__name__).info("Initializing local JSON Database...")

def match_document(doc, query_filter):
    if not query_filter:
        return True
    for key, value in query_filter.items():
        doc_val = doc.get(key)
        if isinstance(value, dict):
            for op, val in value.items():
                if op == "$gt":
                    if doc_val is None or doc_val <= val:
                        return False
                elif op == "$lt":
                    if doc_val is None or doc_val >= val:
                        return False
                elif op == "$exists":
                    exists = key in doc
                    if exists != val:
                        return False
                else:
                    if doc_val != value:
                        return False
        else:
            if isinstance(doc_val, list):
                if value not in doc_val:
                    return False
            else:
                if doc_val != value:
                    return False
    return True

def find_matched_indices(doc, query_filter):
    matched_indices = {}
    for key, value in query_filter.items():
        if "." in key:
            parts = key.split(".")
            list_name = parts[0]
            field_name = parts[1]
            if list_name in doc and isinstance(doc[list_name], list):
                for idx, item in enumerate(doc[list_name]):
                    if isinstance(item, dict) and item.get(field_name) == value:
                        matched_indices[list_name] = idx
                        break
    return matched_indices

def update_document(doc, update_op, matched_index_in_list=None):
    if not update_op:
        return doc

    for op, val in update_op.items():
        if op == "$set":
            for k, v in val.items():
                if "$" in k and matched_index_in_list is not None:
                    parts = k.split(".")
                    list_name = parts[0]
                    field_name = parts[2] if len(parts) > 2 else None
                    if list_name in doc and isinstance(doc[list_name], list):
                        idx = matched_index_in_list.get(list_name, 0)
                        if idx < len(doc[list_name]):
                            if field_name:
                                doc[list_name][idx][field_name] = v
                            else:
                                doc[list_name][idx] = v
                else:
                    doc[k] = v

        elif op == "$unset":
            for k, v in val.items():
                if k in doc:
                    del doc[k]

        elif op == "$push":
            for k, v in val.items():
                if k not in doc:
                    doc[k] = []
                if isinstance(doc[k], list):
                    if isinstance(v, dict) and "$each" in v:
                        doc[k].extend(v["$each"])
                    else:
                        doc[k].append(v)

        elif op == "$pull":
            for k, v in val.items():
                if k in doc and isinstance(doc[k], list):
                    if isinstance(v, dict):
                        new_list = []
                        for item in doc[k]:
                            if isinstance(item, dict):
                                if match_document(item, v):
                                    continue
                            new_list.append(item)
                        doc[k] = new_list
                    else:
                        doc[k] = [item for item in doc[k] if item != v]

        elif op == "$addToSet":
            for k, v in val.items():
                if k not in doc:
                    doc[k] = []
                if isinstance(doc[k], list):
                    if isinstance(v, dict) and "$each" in v:
                        for item in v["$each"]:
                            if item not in doc[k]:
                                doc[k].append(item)
                    else:
                        if v not in doc[k]:
                            doc[k].append(v)

class AsyncJsonCursor:
    def __init__(self, collection, filter_query):
        self.collection = collection
        self.filter_query = filter_query
        self._documents = None
        self.index = 0

    async def _ensure_loaded(self):
        if self._documents is None:
            async with self.collection.lock:
                data = await self.collection._load()
                self._documents = []
                filter_q = self.filter_query or {}
                for doc in data:
                    if match_document(doc, filter_q):
                        self._documents.append(copy.deepcopy(doc))

    def __aiter__(self):
        return self

    async def __anext__(self):
        await self._ensure_loaded()
        if self.index >= len(self._documents):
            raise StopAsyncIteration
        doc = self._documents[self.index]
        self.index += 1
        return doc

    async def to_list(self, length=None):
        await self._ensure_loaded()
        if length is not None:
            return self._documents[:length]
        return self._documents

class AsyncJsonCollection:
    def __init__(self, db_dir, name, db_instance):
        self.db_dir = db_dir
        self.name = name
        self.db_instance = db_instance
        self.file_path = os.path.join(db_dir, f"{name}.json")
        self.lock = asyncio.Lock()
        self._data = None

    async def _load(self):
        if self._data is not None:
            return self._data
        if os.path.exists(self.file_path):
            try:
                loop = asyncio.get_running_loop()
                def _read():
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                self._data = await loop.run_in_executor(None, _read)
            except Exception:
                self._data = []
        else:
            self._data = []

        if not isinstance(self._data, list):
            self._data = []
        return self._data

    async def _save(self):
        if self._data is None:
            return
        loop = asyncio.get_running_loop()
        def _write():
            temp_path = self.file_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.file_path)
        await loop.run_in_executor(None, _write)

    async def find_one(self, filter=None):
        async with self.lock:
            data = await self._load()
            if filter is None:
                filter = {}
            for doc in data:
                if match_document(doc, filter):
                    return copy.deepcopy(doc)
            return None

    async def insert_one(self, document):
        async with self.lock:
            data = await self._load()
            doc_copy = copy.deepcopy(document)
            if "_id" not in doc_copy:
                doc_copy["_id"] = str(uuid.uuid4())
            data.append(doc_copy)
            await self._save()

            class InsertResult:
                def __init__(self, inserted_id):
                    self.inserted_id = inserted_id
            return InsertResult(doc_copy["_id"])

    async def update_one(self, filter, update, upsert=False):
        async with self.lock:
            data = await self._load()
            matched_doc = None
            matched_index = None

            for idx, doc in enumerate(data):
                if match_document(doc, filter):
                    matched_doc = doc
                    matched_index = idx
                    break

            class UpdateResult:
                def __init__(self, matched_count, modified_count):
                    self.matched_count = matched_count
                    self.modified_count = modified_count
                    self.raw_result = {"n": matched_count, "nModified": modified_count, "ok": 1.0}

            if matched_doc is not None:
                matched_indices = find_matched_indices(matched_doc, filter)
                update_document(matched_doc, update, matched_indices)
                await self._save()
                return UpdateResult(1, 1)
            else:
                if upsert:
                    new_doc = {}
                    for k, v in filter.items():
                        if not isinstance(v, dict) and "." not in k:
                            new_doc[k] = v
                    if "_id" not in new_doc:
                        new_doc["_id"] = str(uuid.uuid4())

                    update_document(new_doc, update)
                    data.append(new_doc)
                    await self._save()
                    return UpdateResult(0, 1)
                return UpdateResult(0, 0)

    async def update(self, filter, update, upsert=False, multi=False):
        return await self.update_one(filter, update, upsert=upsert)

    async def delete_one(self, filter):
        async with self.lock:
            data = await self._load()
            matched_index = None
            for idx, doc in enumerate(data):
                if match_document(doc, filter):
                    matched_index = idx
                    break

            class DeleteResult:
                def __init__(self, deleted_count):
                    self.deleted_count = deleted_count

            if matched_index is not None:
                data.pop(matched_index)
                await self._save()
                return DeleteResult(1)
            return DeleteResult(0)

    async def delete_many(self, filter):
        async with self.lock:
            data = await self._load()
            initial_len = len(data)
            data[:] = [doc for doc in data if not match_document(doc, filter)]
            deleted_count = initial_len - len(data)
            await self._save()

            class DeleteResult:
                def __init__(self, deleted_count):
                    self.deleted_count = deleted_count
            return DeleteResult(deleted_count)

    async def count_documents(self, filter):
        async with self.lock:
            data = await self._load()
            count = 0
            for doc in data:
                if match_document(doc, filter):
                    count += 1
            return count

    def find(self, filter=None):
        return AsyncJsonCursor(self, filter)

class AsyncJsonDatabase:
    def __init__(self, db_dir):
        self.db_dir = db_dir
        os.makedirs(db_dir, exist_ok=True)
        self._collections = {}

    def __getattr__(self, name):
        if name not in self._collections:
            self._collections[name] = AsyncJsonCollection(self.db_dir, name, self)
        return self._collections[name]

    def __getitem__(self, name):
        return self.__getattr__(name)

    async def command(self, cmd_name):
        if cmd_name == "dbstats":
            total_size = 0
            collections_count = 0
            objects_count = 0
            for fname in os.listdir(self.db_dir):
                if fname.endswith(".json"):
                    collections_count += 1
                    fpath = os.path.join(self.db_dir, fname)
                    total_size += os.path.getsize(fpath)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                objects_count += len(data)
                    except Exception:
                        pass
            return {
                "dataSize": total_size,
                "storageSize": total_size,
                "collections": collections_count,
                "objects": objects_count
            }
        return {}

class AsyncJsonClient:
    def __init__(self, db_dir="json_db"):
        self.db_dir = db_dir
        os.makedirs(db_dir, exist_ok=True)
        self._databases = {}

    def __getattr__(self, name):
        if name not in self._databases:
            db_path = os.path.join(self.db_dir, name)
            self._databases[name] = AsyncJsonDatabase(db_path)
        return self._databases[name]

    def __getitem__(self, name):
        return self.__getattr__(name)

# Create the instance and make it behaves exactly like mongodb client
_mongo_async_ = AsyncJsonClient()
mongodb = _mongo_async_.Anon
LOGGER(__name__).info("Local JSON Database initialized successfully.")
