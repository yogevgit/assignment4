import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

STORE1 = "http://localhost:5001"
STORE2 = "http://localhost:5002"
ORDER = "http://localhost:5003"

PET_TYPE1 = {"type": "Golden Retriever"}
PET_TYPE2 = {"type": "Australian Shepherd"}
PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE4 = {"type": "bulldog"}

PET1_TYPE1 = {"name": "Lander", "birthdate": "14-05-2020"}
PET2_TYPE1 = {"name": "Lanky"}
PET3_TYPE1 = {"name": "Shelly", "birthdate": "07-07-2019"}
PET4_TYPE2 = {"name": "Felicity", "birthdate": "27-11-2011"}
PET5_TYPE3 = {"name": "Muscles"}
PET6_TYPE3 = {"name": "Junior"}
PET7_TYPE4 = {"name": "Lazy", "birthdate": "07-08-2018"}
PET8_TYPE4 = {"name": "Lemon", "birthdate": "27-03-2020"}


def wait_for_service(base_url: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"Service not ready: {base_url}")


def create_pet_type(base_url: str, payload: Dict[str, Any]) -> str:
    response = requests.post(f"{base_url}/pet-types", json=payload, timeout=5)
    response.raise_for_status()
    return response.json()["id"]


def create_pet(base_url: str, pet_type_id: str, payload: Dict[str, Any]) -> None:
    response = requests.post(
        f"{base_url}/pet-types/{pet_type_id}/pets", json=payload, timeout=5
    )
    response.raise_for_status()


def seed_data() -> Tuple[List[str], List[str]]:
    ids_store1 = [
        create_pet_type(STORE1, PET_TYPE1),
        create_pet_type(STORE1, PET_TYPE2),
        create_pet_type(STORE1, PET_TYPE3),
    ]
    ids_store2 = [
        create_pet_type(STORE2, PET_TYPE1),
        create_pet_type(STORE2, PET_TYPE2),
        create_pet_type(STORE2, PET_TYPE4),
    ]

    create_pet(STORE1, ids_store1[0], PET1_TYPE1)
    create_pet(STORE1, ids_store1[0], PET2_TYPE1)
    create_pet(STORE1, ids_store1[2], PET5_TYPE3)
    create_pet(STORE1, ids_store1[2], PET6_TYPE3)

    create_pet(STORE2, ids_store2[0], PET3_TYPE1)
    create_pet(STORE2, ids_store2[1], PET4_TYPE2)
    create_pet(STORE2, ids_store2[2], PET7_TYPE4)
    create_pet(STORE2, ids_store2[2], PET8_TYPE4)

    return ids_store1, ids_store2


def parse_entries(text: str) -> List[str]:
    entries: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(";") if p.strip()]
        entries.extend(parts)
    return entries


def format_payload(response: requests.Response, success_code: int) -> str:
    if response.status_code != success_code:
        return "NONE"
    try:
        return json.dumps(response.json(), indent=2)
    except ValueError:
        return response.text.strip() or "NONE"


def run_queries(entries: List[str]) -> List[str]:
    output: List[str] = []
    for entry in entries:
        if entry.startswith("query:"):
            body = entry[len("query:") :].strip()
            store_num, query_string = body.split(",", 1)
            store_url = STORE1 if store_num.strip() == "1" else STORE2
            query_string = query_string.strip()
            if "=" in query_string:
                key, value = query_string.split("=", 1)
                params = {key.strip(): value.strip()}
            else:
                params = {}
            response = requests.get(
                f"{store_url}/pet-types", params=params, timeout=5
            )
            payload = format_payload(response, 200)
            output.extend([str(response.status_code), payload, ";"])
        elif entry.startswith("purchase:"):
            body = entry[len("purchase:") :].strip()
            payload_json = json.loads(body)
            response = requests.post(
                f"{ORDER}/purchases", json=payload_json, timeout=5
            )
            payload = format_payload(response, 201)
            output.extend([str(response.status_code), payload, ";"])
        else:
            output.extend(["400", "NONE", ";"])
    return output


def main() -> None:
    wait_for_service(STORE1)
    wait_for_service(STORE2)
    wait_for_service(ORDER)

    seed_data()

    query_path = Path("query.txt")
    if not query_path.exists():
        raise SystemExit("query.txt not found")

    entries = parse_entries(query_path.read_text(encoding="utf-8"))
    response_lines = run_queries(entries)

    Path("response.txt").write_text("\n".join(response_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
