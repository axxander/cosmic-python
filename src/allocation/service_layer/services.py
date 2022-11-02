from __future__ import annotations

from datetime import date
from typing import List

from allocation.domain import model
from allocation.adapters import repository
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    ...


def is_valid_sku(sku: str, batches: List[model.Batch]):
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = model.allocate(line, batches)
        uow.commit()
    return batchref


def reallocate(line: model.OrderLine, uow: AbstractUnitOfWork) -> str:
    """Reallocate an existing order line."""
    with uow:
        batch = uow.batches.get(sku=line.sku)
        if batch is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batch.deallocate(line)
        allocate(line)
        uow.commit()


# def change_batch_quantity(batchref:str, new_qty: int, uow: AbstractUnitOfWork):
#     with uow:
#         batch = uow.batches.get(reference=batchref)
#         batch.change_purchased_quantity(new_qty)
#         while batch.available_quantity < 0:
#             batch.deallocate_one()
#         uow.commit()


def add_batch(ref: str, sku: str, qty: int, eta: date | None, uow: AbstractUnitOfWork):
    with uow:
        batch = model.Batch(ref, sku, qty, eta)
        uow.batches.add(batch)
        uow.commit()
