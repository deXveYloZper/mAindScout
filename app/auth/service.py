# app/auth/service.py

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from pymongo.database import Database
from fastapi import Depends
from starlette.concurrency import run_in_threadpool
from app.auth.models import User, UserCreate, UserUpdate
from app.auth.utils import verify_password, get_password_hash, create_user_token
from app.core.database import get_database
import uuid

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Database = Depends(get_database)):
        self.db = db
        self.users_collection = self.db['users']

    async def create_user(self, user_data: UserCreate) -> User:
        existing_user = await run_in_threadpool(self.users_collection.find_one, {"email": user_data.email})
        if existing_user:
            raise ValueError("User with this email already exists")
        user_doc = {
            "_id": str(uuid.uuid4()),
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role.value,
            "is_active": user_data.is_active,
            "organization": user_data.organization,
            "hashed_password": get_password_hash(user_data.password),
            "created_at": datetime.utcnow(),
            "last_login": None,
            "failed_login_attempts": 0,
            "locked_until": None
        }
        await run_in_threadpool(self.users_collection.insert_one, user_doc)
        user_doc['id'] = user_doc.pop('_id')
        user_doc.pop("hashed_password", None)
        return User(**user_doc)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user_doc = await run_in_threadpool(self.users_collection.find_one, {"email": email})
        if not user_doc: return None
        if user_doc.get("locked_until") and datetime.utcnow() < user_doc["locked_until"]:
            return None
        if not verify_password(password, user_doc["hashed_password"]):
            await run_in_threadpool(self._increment_failed_attempts, user_doc["_id"])
            return None
        await self._reset_failed_attempts(user_doc["_id"])
        await run_in_threadpool(self.users_collection.update_one, {"_id": user_doc["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
        user_doc['id'] = user_doc.pop('_id')
        user_doc.pop("hashed_password", None)
        return User(**user_doc)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        user_doc = await run_in_threadpool(self.users_collection.find_one, {"_id": user_id})
        if not user_doc: return None
        user_doc['id'] = user_doc.pop('_id')
        user_doc.pop("hashed_password", None)
        return User(**user_doc)

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        update_data = {}
        if user_data.full_name is not None:
            update_data["full_name"] = user_data.full_name
        if user_data.role is not None:
            update_data["role"] = user_data.role.value
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
        if user_data.organization is not None:
            update_data["organization"] = user_data.organization
        if not update_data:
            return await self.get_user_by_id(user_id)
        result = await run_in_threadpool(self.users_collection.update_one, {"_id": user_id}, {"$set": update_data})
        if result.modified_count == 0:
            return None
        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: str) -> bool:
        result = await run_in_threadpool(self.users_collection.delete_one, {"_id": user_id})
        return result.deleted_count > 0

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        users = []
        cursor = await run_in_threadpool(lambda: list(self.users_collection.find().skip(skip).limit(limit)))
        for user_doc in cursor:
            user_doc['id'] = user_doc.pop('_id')
            user_doc.pop("hashed_password", None)
            users.append(User(**user_doc))
        return users

    def create_access_token_for_user(self, user: User) -> str:
        """Create an access token for a user."""
        return create_user_token(user_id=str(user.id), email=user.email, role=user.role.value)

    async def _increment_failed_attempts(self, user_id: str):
        user_doc = await run_in_threadpool(self.users_collection.find_one, {"_id": user_id})
        if not user_doc:
            return
        failed_attempts = user_doc.get("failed_login_attempts", 0) + 1
        locked_until = None
        if failed_attempts >= 5:
            locked_until = datetime.utcnow() + timedelta(minutes=30)
        await run_in_threadpool(self.users_collection.update_one,
            {"_id": user_id},
            {"$set": {"failed_login_attempts": failed_attempts, "locked_until": locked_until}})

    async def _reset_failed_attempts(self, user_id: str):
        await run_in_threadpool(self.users_collection.update_one,
            {"_id": user_id},
            {"$set": {"failed_login_attempts": 0, "locked_until": None}})

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        user_doc = await run_in_threadpool(self.users_collection.find_one, {"_id": user_id})
        if not user_doc:
            raise ValueError("User not found")
        if not verify_password(current_password, user_doc["hashed_password"]):
            raise ValueError("Incorrect current password")
        new_hashed_password = get_password_hash(new_password)
        await run_in_threadpool(self.users_collection.update_one, {"_id": user_id}, {"$set": {"hashed_password": new_hashed_password}})
        return True 