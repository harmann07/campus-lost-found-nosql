import os
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import redis
from redis.exceptions import RedisError

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DB = os.getenv("MONGODB_DB", "campus_lost_found").strip()
REDIS_URL = os.getenv("REDIS_URL", "").strip()
CACHE_KEY = "campus_lost_found:items"
CACHE_TTL_SECONDS = 60

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is missing. Add it to your .env file.")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL is missing. Add it to your .env file.")

mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=8000)
db = mongo_client[MONGODB_DB]
items_collection = db["items"]
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=5)

templates = Jinja2Templates(directory="templates")
app = FastAPI(title="Campus Lost & Found Portal")
app.mount("/static", StaticFiles(directory="static"), name="static")


def clear_items_cache():
    """Redis stores a short-lived copy of the MongoDB item list."""
    try:
        redis_client.delete(CACHE_KEY)
    except RedisError:
        # The next request can rebuild the cache. MongoDB remains the source of truth.
        pass


def get_items():
    """Read from Redis cache first; if absent, read MongoDB and cache the result."""
    try:
        cached = redis_client.get(CACHE_KEY)
        if cached:
            return json.loads(cached), "Redis cache"
    except RedisError:
        pass

    docs = list(items_collection.find().sort("_id", -1))
    for item in docs:
        item["id"] = str(item.pop("_id"))
    try:
        redis_client.setex(CACHE_KEY, CACHE_TTL_SECONDS, json.dumps(docs, default=str))
    except RedisError:
        pass
    return docs, "MongoDB"


@app.get("/", response_class=HTMLResponse)
def home(request: Request, message: str = ""):
    try:
        items, source = get_items()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"items": items, "source": source, "message": message},
        )
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to MongoDB. Check MONGODB_URI in your .env file."
        )


@app.post("/add")
def add_item(
    item_name: str = Form(...),
    item_type: str = Form(...),
    location: str = Form(...),
    description: str = Form(""),
    contact: str = Form(...),
):
    item = {
        "item_name": item_name.strip(),
        "item_type": item_type.strip(),
        "location": location.strip(),
        "description": description.strip(),
        "contact": contact.strip(),
        "status": "Open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not item["item_name"] or not item["location"] or not item["contact"]:
        raise HTTPException(status_code=400, detail="Name, location, and contact are required.")
    try:
        items_collection.insert_one(item)
        clear_items_cache()
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Could not save item to MongoDB.")
    return RedirectResponse(url="/?message=Item+report+added+successfully", status_code=303)


@app.post("/resolve/{item_id}")
def resolve_item(item_id: str):
    from bson import ObjectId
    try:
        result = items_collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": {"status": "Resolved"}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Item not found.")
        clear_items_cache()
    except PyMongoError:
        raise HTTPException(status_code=503, detail="Could not update item in MongoDB.")
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=400, detail="Invalid item ID.")
    return RedirectResponse(url="/?message=Item+marked+as+resolved", status_code=303)


@app.get("/health")
def health():
    result = {"app": "ok"}
    try:
        mongo_client.admin.command("ping")
        result["mongodb"] = "connected"
    except Exception:
        result["mongodb"] = "disconnected"
    try:
        redis_client.ping()
        result["redis"] = "connected"
    except Exception:
        result["redis"] = "disconnected"
    result["redis_role"] = "Caches item list for 60 seconds"
    return result
