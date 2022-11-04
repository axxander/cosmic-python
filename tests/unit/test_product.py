from datetime import (
    date,
    timedelta,
)
import pytest

from allocation.domain.model import (
    Batch,
    OrderLine,
    OutOfStock,
    Product,
)


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_prefers_warehouse_batches_to_shipments():
    warehouse_batch = Batch("in-stock-batch", "YELLOW-CHAIR", 10, None)
    shipment_batch = Batch("shipment-batch", "YELLOW-CHAIR", 10, tomorrow)
    product = Product(sku="YELLOW-CHAIR", batches=[warehouse_batch, shipment_batch])
    line = OrderLine("order-ref", "YELLOW-CHAIR", 5)

    product.allocate(line)
    
    assert warehouse_batch.available_quantity == 5
    assert shipment_batch.available_quantity == 10


def test_prefers_earliest_batch():
    earliest = Batch("earlier-batch", "YELLOW-CHAIR", 10, today)
    medium = Batch("medium-batch", "YELLOW-CHAIR", 10, tomorrow)
    latest = Batch("latest-batch", "YELLOW-CHAIR", 10, later)
    product = Product(sku="YELLOW-CHAIR", batches=[earliest, medium, latest])
    line = OrderLine("order-ref", "YELLOW-CHAIR", 5)
    
    product.allocate(line)

    assert earliest.available_quantity == 5
    assert medium.available_quantity == 10
    assert latest.available_quantity == 10


def test_return_allocated_batch_ref():
    warehouse_batch = Batch("in-stock-batch", "YELLOW-CHAIR", 10, None)
    shipment_batch = Batch("shipment-batch", "YELLOW-CHAIR", 10, tomorrow)
    product = Product(sku="YELLOW-CHAIR", batches=[warehouse_batch, shipment_batch])
    line = OrderLine("order-ref", "YELLOW-CHAIR", 2)

    allocation = product.allocate(line)
    
    assert allocation == warehouse_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=today)
    product = Product(sku="SMALL-FORK", batches=[batch])
    line1 = OrderLine("order1", "SMALL-FORK", 10)
    product.allocate(line1)

    line2 = OrderLine("order2", "SMALL-FORK", 1)
    with pytest.raises(OutOfStock, match="SMALL-FORK"):
        product.allocate(line2)

    
def test_increments_version_number():
    line = OrderLine("oref", "SCANDI-PEN", 10)
    product = Product(sku="SCANDI-PEN", batches=[Batch("b1", "SCANDI-PEN", 100, eta=None)])
    product.version_number = 7
    product.allocate(line)
    assert product.version_number == 8
