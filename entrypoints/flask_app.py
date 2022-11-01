from datetime import datetime
import logging

from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from domain import model
from adapters import (
    orm,
    repository,
)
from service_layer import services


orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    orderid, sku, qty = request.json["orderid"], request.json["sku"], request.json["qty"]

    try:
        batchref = services.allocate(orderid, sku, qty, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    session.commit()

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["POST"])
def add_batch():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    services.add_batch(
        request.json["ref"],
        request.json["sku"],
        request.json["qty"],
        eta,
        repo,
        session,
    )

    return "OK", 201


@app.route("/health", methods=["GET"])
def health_endpoint():
    return 'success', 200