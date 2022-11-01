from datetime import (
    date,
    timedelta,
)

import pytest

from domain import model
from service_layer import services
from adapters import repository


today = date.today()
tomorrow = today + timedelta(days=1)

class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)

    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        """Factory function used to instantiate batch and add to repo."""
        return FakeRepository(
            [
                model.Batch(ref, sku, qty, eta),
            ]
        )


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_return_allocation():
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    repo = FakeRepository.for_batch("b1", "AREALSKU", 100, eta=None)  # using factory instead

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())

def test_allocate_errors_for_invalid_sku():
    """Same as above, but shown by doing it a different way."""
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)  # use service instead

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())


def test_commits():
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate("o1", "OMINOUS-MIRROR", 10, repo, session)

    assert session.committed is True


# Domain-layer test:
def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = model.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = model.OrderLine("oref", "RETRO-CLOCK", 10)

    model.allocate(line, [in_stock_batch, shipment_batch])  # using domain directly

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100

# Service-layer test:
def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = model.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()

    services.allocate("oref", "RETRO-CLOCK", 10, repo, session)  # using domain via a allocate service

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100
    

def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)

    assert repo.get("b1") is not None
    assert session.committed
