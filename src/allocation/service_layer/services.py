from __future__ import annotations

from datetime import date
from typing import List

from allocation.domain import model
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    ...


def is_valid_sku(sku: str, batches: List[model.Batch]):
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def add_batch(ref: str, sku: str, qty: int, eta: date | None, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:  # no batches for the given SKU
            product = model.Product(sku, batches=[])
            uow.products.add(product)
        batch = model.Batch(ref, sku, qty, eta)
        product.batches.append(batch)
        uow.commit()
