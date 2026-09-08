import pytest
from tests.credentials import ADMIN_AUTH, ADMIN_PASSWORD, ADMIN_USERNAME

CAKE_DATA = {
    "name": "Медовик",
    "description": "Медові коржі зі сметанним кремом",
    "price_kopiyky": 95000,
    "weight_grams": 1200,
    "is_available": True,
}


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/admin/cakes"),
        ("GET", "/admin/cakes/1"),
        ("POST", "/admin/cakes"),
        ("PUT", "/admin/cakes/1"),
    ],
)
def test_admin_routes_require_credentials(client, method, path):
    response = client.request(method, path, json=CAKE_DATA)

    assert response.status_code == 401


@pytest.mark.parametrize(
    "auth",
    [
        (ADMIN_USERNAME, "wrong-password"),
        ("wrong-admin", ADMIN_PASSWORD),
    ],
)
def test_invalid_credentials_are_rejected(client, auth):
    response = client.get("/admin/cakes", auth=auth)

    assert response.status_code == 401


def test_admin_can_create_public_cake(client):
    response = client.post(
        "/admin/cakes",
        json=CAKE_DATA,
        auth=ADMIN_AUTH,
    )

    assert response.status_code == 201
    cake_id = response.json()["id"]

    public_response = client.get(f"/cakes/{cake_id}")

    assert public_response.status_code == 200
    assert public_response.json()["name"] == CAKE_DATA["name"]
    assert public_response.json()["price_kopiyky"] == 95000


def test_hidden_cake_can_be_seen_by_admin_and_reenabled(client):
    hidden_cake = {**CAKE_DATA, "is_available": False}

    response = client.post(
        "/admin/cakes",
        json=hidden_cake,
        auth=ADMIN_AUTH,
    )

    assert response.status_code == 201
    cake_id = response.json()["id"]

    public_list = client.get("/cakes")
    assert public_list.status_code == 200
    assert public_list.json() == []
    assert client.get(f"/cakes/{cake_id}").status_code == 404

    admin_response = client.get(
        f"/admin/cakes/{cake_id}",
        auth=ADMIN_AUTH,
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["is_available"] is False

    update_response = client.put(
        f"/admin/cakes/{cake_id}",
        json=CAKE_DATA,
        auth=ADMIN_AUTH,
    )
    assert update_response.status_code == 200

    public_list = client.get("/cakes")
    assert public_list.status_code == 200
    assert [cake["id"] for cake in public_list.json()] == [cake_id]
    assert client.get(f"/cakes/{cake_id}").status_code == 200