from typing import List

from domain import model
from adapters import repository


class InvalidSku(Exception):
    ...


def is_valid_sku(sku: str, batches: List[model.Batch]):
    return sku in {b.sku for b in batches}


def allocate(line: model.OrderLine, repo: repository.AbstractRepository, session) -> str:
    batches = repo.list()  # fetch objects from repository
    if not is_valid_sku(line.sku, batches):  # checks and assertions
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)  # call domain service
    session.commit()  # happy path: commit changes
    return batchref
    