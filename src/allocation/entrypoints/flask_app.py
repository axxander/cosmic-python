from datetime import datetime
import logging

from flask import Flask, request

from allocation.domain import model
from allocation.adapters import orm
from allocation.service_layer import services, unit_of_work


orm.start_mappers()
app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    orderid, sku, qty = request.json["orderid"], request.json["sku"], request.json["qty"]

    try:
        batchref = services.allocate(orderid, sku, qty, uow)
    except (model.OutOfStock, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["POST"])
def add_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    services.add_batch(
        request.json["ref"],
        request.json["sku"],
        request.json["qty"],
        eta,
        uow,
    )

    return "OK", 201


@app.route("/health", methods=["GET"])
def health_endpoint():
    return 'success', 200