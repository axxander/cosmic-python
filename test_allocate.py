from datetime import (
    date,
    timedelta,
)
import pytest

from model import (
    allocate,
    Batch,
    OrderLine,
    OutOfStock,
)


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch = Batch("batch-001", "RED-CHAIR", 10, today)
    line = OrderLine("order-ref", "RED-CHAIR", 2)

    allocate(line, [batch])

    assert batch.available_quantity == 8


def test_cannot_allocate_if_available_smaller_than_required():
    batch = Batch("batch-001", "GREEN-CHAIR", 2, today)
    line = OrderLine("order-ref", "GREEN-CHAIR", 6)

    with pytest.raises(OutOfStock):
        allocate(line, [batch])

def test_can_allocate_if_available_equal_to_required():
    batch = Batch("batch-001", "BLUE-CHAIR", 6, today)
    line = OrderLine("order-ref", "BLUE-CHAIR", 6)

    allocate(line, [batch])

def test_prefers_warehouse_batches_to_shipment():
    warehouse_batch = Batch("batch-001", "YELLOW-CHAIR", 10, None)
    shipment_batch = Batch("batch-001", "YELLOW-CHAIR", 10, tomorrow)
    line = OrderLine("order-ref", "YELLOW-CHAIR", 6)

    allocate(line, [shipment_batch, warehouse_batch])
    
    assert warehouse_batch.available_quantity == 4
    assert shipment_batch.available_quantity == 10

def test_prefers_earliest_batch():
    earliest = Batch("batch-001", "YELLOW-CHAIR", 10, today)
    medium = Batch("batch-002", "YELLOW-CHAIR", 10, tomorrow)
    latest = Batch("batch-003", "YELLOW-CHAIR", 10, later)
    line = OrderLine("order-ref", "YELLOW-CHAIR", 6)
    
    allocate(line, [medium, latest, earliest])

    assert earliest.available_quantity == 4
    assert medium.available_quantity == 10
    assert latest.available_quantity == 10

def test_return_allocated_batch_ref():
    in_stock_batch = Batch("batch-001", "YELLOW-CHAIR", 10, None)
    shipment_batch = Batch("batch-001", "YELLOW-CHAIR", 10, later)
    line = OrderLine("order-ref", "YELLOW-CHAIR", 2)

    allocation = allocate(line, [shipment_batch, in_stock_batch])
    
    assert allocation == in_stock_batch.reference
