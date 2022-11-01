import uuid

import pytest
import requests

import config
import model


def random_suffix():
    return uuid.uuid4().hex[:6]

def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"

def random_batchref(name=""):
    return f"batch-{name}-{random_suffix()}"

def random_orderid(name=""):
    return f"order-{name}-{random_suffix()}"


@pytest.mark.usefixtures("restart_api")
def test_happy_path_return_201_and_allocated_batch(add_stock, postgres_session):
    sku, othersku = random_sku(), random_sku(name="other")
    earlybatch = random_batchref(name="1")
    laterbatch = random_batchref(name="2")
    otherbatch = random_batchref(name="3")
    # helper fixture that hides detail of inserting into tables
    add_stock(
        [
            (laterbatch, sku, 100, "2011-01-02"),
            (earlybatch, sku, 100, "2011-01-01"),
            (otherbatch, othersku, 100, None),
        ]
    )

    line = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=line)

    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_return_400_and_error_message():
    unknown_sku, orderid = random_sku(), random_orderid()
    line = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=line)

    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"