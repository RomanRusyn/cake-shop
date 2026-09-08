from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from models import Order, OrderItem
from tests.credentials import ADMIN_AUTH


def create_cake(client, **changes):
    data = {
        "name": "Медовик",
        "description": "Медові коржі зі сметанним кремом",
        "price_kopiyky": 95000,
        "weight_grams": 1200,
        "is_available": True,
    }
    data.update(changes)

    response = client.post(
        "/admin/cakes",
        json=data,
        auth=ADMIN_AUTH,
    )
    assert response.status_code == 201, response.text

    return response.json()


def order_payload(items):
    tomorrow = (
        datetime.now(ZoneInfo("Europe/Kyiv")).date()
        + timedelta(days=1)
    )

    return {
        "customer_name": "Тестове замовлення",
        "customer_phone": "+380501234567",
        "requested_date": tomorrow.isoformat(),
        "items": items,
    }


def test_order_total_and_saved_cake_details(client):
    honey = create_cake(client)
    chocolate = create_cake(
        client,
        name="Шоколадний торт",
        price_kopiyky=120000,
    )

    response = client.post(
        "/orders",
        json=order_payload([
            {"cake_id": honey["id"], "quantity": 2},
            {"cake_id": chocolate["id"], "quantity": 1},
        ]),
    )

    assert response.status_code == 201, response.text
    order = response.json()

    assert order["status"] == "new"
    assert len(order["items"]) == 2
    assert order["total_kopiyky"] == 310000

    # Change the catalogue after the purchase.
    update_response = client.put(
        f"/admin/cakes/{honey['id']}",
        auth=ADMIN_AUTH,
        json={
            "name": "Медовик оновлений",
            "description": "Новий опис",
            "price_kopiyky": 150000,
            "weight_grams": 1600,
            "is_available": True,
        },
    )
    assert update_response.status_code == 200

    saved_response = client.get(
        f"/admin/orders/{order['id']}",
        auth=ADMIN_AUTH,
    )
    assert saved_response.status_code == 200

    saved_order = saved_response.json()
    saved_honey = next(
        item
        for item in saved_order["items"]
        if item["cake_id"] == honey["id"]
    )

    assert saved_honey["cake_name"] == "Медовик"
    assert saved_honey["unit_price_kopiyky"] == 95000
    assert saved_honey["weight_grams"] == 1200
    assert saved_honey["quantity"] == 2
    assert saved_honey["subtotal_kopiyky"] == 190000
    assert saved_order["total_kopiyky"] == 310000


@pytest.mark.parametrize("invalid_kind", ["missing", "unavailable"])
def test_invalid_item_saves_no_order(client, db_session, invalid_kind):
    available = create_cake(client)

    if invalid_kind == "unavailable":
        hidden = create_cake(client, is_available=False)
        invalid_id = hidden["id"]
    else:
        invalid_id = available["id"] + 1000

    response = client.post(
        "/orders",
        json=order_payload([
            {"cake_id": available["id"], "quantity": 1},
            {"cake_id": invalid_id, "quantity": 1},
        ]),
    )

    assert response.status_code == 400

    order_count = db_session.scalar(
        select(func.count()).select_from(Order)
    )
    item_count = db_session.scalar(
        select(func.count()).select_from(OrderItem)
    )

    assert order_count == 0
    assert item_count == 0


def test_customer_cannot_supply_price(client, db_session):
    cake = create_cake(client)

    response = client.post(
        "/orders",
        json=order_payload([
            {
                "cake_id": cake["id"],
                "quantity": 1,
                "unit_price_kopiyky": 1,
            }
        ]),
    )

    assert response.status_code == 422
    assert db_session.scalar(
        select(func.count()).select_from(Order)
    ) == 0


def test_order_details_require_admin(client):
    cake = create_cake(client)

    response = client.post(
        "/orders",
        json=order_payload([
            {"cake_id": cake["id"], "quantity": 1}
        ]),
    )
    assert response.status_code == 201
    order_id = response.json()["id"]

    anonymous_response = client.get(f"/admin/orders/{order_id}")
    assert anonymous_response.status_code == 401

    admin_response = client.get(
        f"/admin/orders/{order_id}",
        auth=ADMIN_AUTH,
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["customer_name"] == "Тестове замовлення"


def test_order_moves_through_preparation(client):
    cake = create_cake(client)
    response = client.post(
        "/orders",
        json=order_payload([
            {"cake_id": cake["id"], "quantity": 1}
        ]),
    )
    assert response.status_code == 201
    order_id = response.json()["id"]

    for next_status in [
        "confirmed",
        "in_preparation",
        "ready",
        "completed",
    ]:
        response = client.patch(
            f"/admin/orders/{order_id}/status",
            json={"status": next_status},
            auth=ADMIN_AUTH,
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == next_status

        saved = client.get(
            f"/admin/orders/{order_id}",
            auth=ADMIN_AUTH,
        )
        assert saved.status_code == 200
        assert saved.json()["status"] == next_status


def test_invalid_transition_preserves_status(client):
    cake = create_cake(client)
    response = client.post(
        "/orders",
        json=order_payload([
            {"cake_id": cake["id"], "quantity": 1}
        ]),
    )
    assert response.status_code == 201
    order_id = response.json()["id"]

    # A new order cannot jump directly to completed.
    rejected = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "completed"},
        auth=ADMIN_AUTH,
    )
    assert rejected.status_code == 409

    saved = client.get(
        f"/admin/orders/{order_id}",
        auth=ADMIN_AUTH,
    )
    assert saved.status_code == 200
    assert saved.json()["status"] == "new"

    # Repeating the current status is allowed.
    repeated = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "new"},
        auth=ADMIN_AUTH,
    )
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "new"

    # An unknown status is rejected by schema validation.
    invalid = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "banana"},
        auth=ADMIN_AUTH,
    )
    assert invalid.status_code == 422


def test_cancelled_order_cannot_be_reopened(client):
    cake = create_cake(client)
    response = client.post(
        "/orders",
        json=order_payload([
            {"cake_id": cake["id"], "quantity": 1}
        ]),
    )
    assert response.status_code == 201
    order_id = response.json()["id"]

    cancelled = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "cancelled"},
        auth=ADMIN_AUTH,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    reopened = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "confirmed"},
        auth=ADMIN_AUTH,
    )
    assert reopened.status_code == 409

    saved = client.get(
        f"/admin/orders/{order_id}",
        auth=ADMIN_AUTH,
    )
    assert saved.status_code == 200
    assert saved.json()["status"] == "cancelled"


def test_admin_order_list_filters_and_paginates(client):
    cake = create_cake(client)
    order_ids = []

    for _ in range(3):
        response = client.post(
            "/orders",
            json=order_payload([
                {"cake_id": cake["id"], "quantity": 1}
            ]),
        )
        assert response.status_code == 201
        order_ids.append(response.json()["id"])

    confirmed = client.patch(
        f"/admin/orders/{order_ids[1]}/status",
        json={"status": "confirmed"},
        auth=ADMIN_AUTH,
    )
    assert confirmed.status_code == 200

    filtered = client.get(
        "/admin/orders",
        params={"status": "new"},
        auth=ADMIN_AUTH,
    )
    assert filtered.status_code == 200
    assert [order["id"] for order in filtered.json()] == [
        order_ids[2],
        order_ids[0],
    ]

    page = client.get(
        "/admin/orders",
        params={"status": "new", "limit": 1, "offset": 1},
        auth=ADMIN_AUTH,
    )
    assert page.status_code == 200
    assert [order["id"] for order in page.json()] == [order_ids[0]]


def test_order_list_and_status_update_require_admin(client):
    cake = create_cake(client)
    response = client.post(
        "/orders",
        json=order_payload([
            {"cake_id": cake["id"], "quantity": 1}
        ]),
    )
    assert response.status_code == 201
    order_id = response.json()["id"]

    assert client.get("/admin/orders").status_code == 401

    unauthorized = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "confirmed"},
    )
    assert unauthorized.status_code == 401

    saved = client.get(
        f"/admin/orders/{order_id}",
        auth=ADMIN_AUTH,
    )
    assert saved.status_code == 200
    assert saved.json()["status"] == "new"
