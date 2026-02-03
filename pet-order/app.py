import os
from datetime import datetime
from typing import Any, Dict

from bson import ObjectId
from flask import Flask, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "pet_order")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
purchases = db["purchases"]


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()}), 200


@app.post("/purchases")
def create_purchase() -> Any:
    payload = request.get_json(silent=True) or {}
    required = ["purchaser", "pet-type", "purchase-id"]
    missing = [key for key in required if key not in payload]
    if missing:
        return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400

    if "pet-name" in payload and "store" not in payload:
        return jsonify({"error": "pet-name requires store"}), 400

    document = {
        "purchaser": payload["purchaser"],
        "pet-type": payload["pet-type"],
        "purchase-id": payload["purchase-id"],
    }
    if "store" in payload:
        document["store"] = payload["store"]
    if "pet-name" in payload:
        document["pet-name"] = payload["pet-name"]

    result = purchases.insert_one(document)
    document["id"] = str(result.inserted_id)
    return jsonify(document), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
