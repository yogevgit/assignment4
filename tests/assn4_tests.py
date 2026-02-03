import time

import requests

STORE1 = "http://localhost:5001"
STORE2 = "http://localhost:5002"
ORDER = "http://localhost:5003"

PET_TYPE1 = {"type": "Golden Retriever"}
PET_TYPE1_VAL = {
    "type": "Golden Retriever",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": [],
    "lifespan": 12,
}
PET_TYPE2 = {"type": "Australian Shepherd"}
PET_TYPE2_VAL = {
    "type": "Australian Shepherd",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": ["Loyal", "outgoing", "and", "friendly"],
    "lifespan": 15,
}
PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE3_VAL = {
    "type": "Abyssinian",
    "family": "Felidae",
    "genus": "Felis",
    "attributes": ["Intelligent", "and", "curious"],
    "lifespan": 13,
}
PET_TYPE4 = {"type": "bulldog"}
PET_TYPE4_VAL = {
    "type": "bulldog",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": ["Gentle", "calm", "and", "affectionate"],
    "lifespan": None,
}

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


def assert_fields(actual, expected):
    for key, value in expected.items():
        assert actual.get(key) == value


def test_assignment4_flow():
    wait_for_service(STORE1)
    wait_for_service(STORE2)
    wait_for_service(ORDER)

    ids_store1 = []
    for payload, expected in [
        (PET_TYPE1, PET_TYPE1_VAL),
        (PET_TYPE2, PET_TYPE2_VAL),
        (PET_TYPE3, PET_TYPE3_VAL),
    ]:
        response = requests.post(f"{STORE1}/pet-types", json=payload, timeout=5)
        assert response.status_code == 201
        body = response.json()
        assert "id" in body
        assert_fields(body, expected)
        ids_store1.append(body["id"])

    ids_store2 = []
    for payload, expected in [
        (PET_TYPE1, PET_TYPE1_VAL),
        (PET_TYPE2, PET_TYPE2_VAL),
        (PET_TYPE4, PET_TYPE4_VAL),
    ]:
        response = requests.post(f"{STORE2}/pet-types", json=payload, timeout=5)
        assert response.status_code == 201
        body = response.json()
        assert "id" in body
        assert_fields(body, expected)
        ids_store2.append(body["id"])

    assert len(set(ids_store1)) == len(ids_store1)
    assert len(set(ids_store2)) == len(ids_store2)

    id_1, id_2, id_3 = ids_store1
    id_4, id_5, id_6 = ids_store2

    for payload in [PET1_TYPE1, PET2_TYPE1]:
        response = requests.post(
            f"{STORE1}/pet-types/{id_1}/pets", json=payload, timeout=5
        )
        assert response.status_code == 201

    for payload in [PET5_TYPE3, PET6_TYPE3]:
        response = requests.post(
            f"{STORE1}/pet-types/{id_3}/pets", json=payload, timeout=5
        )
        assert response.status_code == 201

    response = requests.post(
        f"{STORE2}/pet-types/{id_4}/pets", json=PET3_TYPE1, timeout=5
    )
    assert response.status_code == 201

    response = requests.post(
        f"{STORE2}/pet-types/{id_5}/pets", json=PET4_TYPE2, timeout=5
    )
    assert response.status_code == 201

    for payload in [PET7_TYPE4, PET8_TYPE4]:
        response = requests.post(
            f"{STORE2}/pet-types/{id_6}/pets", json=payload, timeout=5
        )
        assert response.status_code == 201

    response = requests.get(f"{STORE1}/pet-types/{id_2}", timeout=5)
    assert response.status_code == 200
    body = response.json()
    assert_fields(body, PET_TYPE2_VAL)

    response = requests.get(f"{STORE2}/pet-types/{id_6}/pets", timeout=5)
    assert response.status_code == 200
    pets = response.json()
    assert any(pet.get("name") == PET7_TYPE4["name"] for pet in pets)
    assert any(pet.get("name") == PET8_TYPE4["name"] for pet in pets)
