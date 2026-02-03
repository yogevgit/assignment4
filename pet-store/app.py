import os
from datetime import datetime
from typing import Any, Dict, List

from bson import ObjectId
from flask import Flask, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "pet_store")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
pet_types = db["pet_types"]
pets = db["pets"]

PET_TYPE_MAP: Dict[str, Dict[str, Any]] = {
    "Golden Retriever": {
        "family": "Canidae",
        "genus": "Canis",
        "attributes": [],
        "lifespan": 12,
    },
    "Australian Shepherd": {
        "family": "Canidae",
        "genus": "Canis",
        "attributes": ["Loyal", "outgoing", "and", "friendly"],
        "lifespan": 15,
    },
    "Abyssinian": {
        "family": "Felidae",
        "genus": "Felis",
        "attributes": ["Intelligent", "and", "curious"],
        "lifespan": 13,
    },
    "bulldog": {
        "family": "Canidae",
        "genus": "Canis",
        "attributes": ["Gentle", "calm", "and", "affectionate"],
        "lifespan": None,
    },
}


def to_object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except Exception:
        return None


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()}), 200


@app.post("/pet-types")
def create_pet_type() -> Any:
    payload = request.get_json(silent=True) or {}
    pet_type_name = payload.get("type")
    if not pet_type_name:
        return jsonify({"error": "type is required"}), 400

    defaults = PET_TYPE_MAP.get(
        pet_type_name,
        {"family": None, "genus": None, "attributes": [], "lifespan": None},
    )
    document = {
        "type": pet_type_name,
        "family": defaults["family"],
        "genus": defaults["genus"],
        "attributes": list(defaults["attributes"]),
        "lifespan": defaults["lifespan"],
    }
    result = pet_types.insert_one(document)
    response = dict(document)
    response.pop("_id", None)
    response["id"] = str(result.inserted_id)
    return jsonify(response), 201


@app.get("/pet-types")
def query_pet_types() -> Any:
    allowed_fields = {"type", "family", "genus", "lifespan"}
    filters: Dict[str, Any] = {}
    for key, value in request.args.items():
        if key not in allowed_fields:
            return jsonify({"error": f"invalid query field: {key}"}), 400
        if key == "lifespan":
            try:
                filters[key] = int(value)
            except ValueError:
                return jsonify({"error": "lifespan must be an integer"}), 400
        else:
            filters[key] = value

    results: List[Dict[str, Any]] = [
        serialize_doc(doc) for doc in pet_types.find(filters)
    ]
    return jsonify(results), 200


@app.get("/pet-types/<pet_type_id>")
def get_pet_type(pet_type_id: str) -> Any:
    object_id = to_object_id(pet_type_id)
    if not object_id:
        return jsonify({"error": "invalid id"}), 400
    doc = pet_types.find_one({"_id": object_id})
    if not doc:
        return jsonify({"error": "not found"}), 404
    return jsonify(serialize_doc(doc)), 200


@app.post("/pet-types/<pet_type_id>/pets")
def create_pet(pet_type_id: str) -> Any:
    object_id = to_object_id(pet_type_id)
    if not object_id:
        return jsonify({"error": "invalid id"}), 400
    if not pet_types.find_one({"_id": object_id}):
        return jsonify({"error": "pet type not found"}), 404

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    document = {
        "pet_type_id": object_id,
        "name": name,
        "birthdate": payload.get("birthdate"),
    }
    result = pets.insert_one(document)
    response = dict(document)
    response.pop("_id", None)
    response["id"] = str(result.inserted_id)
    response["pet_type_id"] = str(object_id)
    return jsonify(response), 201


@app.get("/pet-types/<pet_type_id>/pets")
def list_pets(pet_type_id: str) -> Any:
    object_id = to_object_id(pet_type_id)
    if not object_id:
        return jsonify({"error": "invalid id"}), 400
    docs = pets.find({"pet_type_id": object_id})
    response = []
    for doc in docs:
        item = {
            "id": str(doc["_id"]),
            "name": doc.get("name"),
            "birthdate": doc.get("birthdate"),
        }
        response.append(item)
    return jsonify(response), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
