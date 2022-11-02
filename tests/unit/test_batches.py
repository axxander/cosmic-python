from datetime import date
from typing import Tuple

import pytest

from allocation.domain.model import (
    Batch,
    OrderLine,
)


def make_batch_and_line(sku: str, batch_qty: int, line_qty: int) -> Tuple[Batch, OrderLine]:
    return (
        Batch("batch-001", sku, batch_qty, eta=date.today()),
        OrderLine("order-123", sku, line_qty),
    )


def test_can_allocate_if_available_greater_than_required():
    large_batch, small_line = make_batch_and_line("RED-CHAIR", 20, 2)
    assert large_batch.can_allocate(small_line)

def test_can_allocate_if_available_smaller_than_required():
    large_batch, small_line = make_batch_and_line("RED-CHAIR", 2, 20)
    assert large_batch.can_allocate(small_line) is False

def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line("RED-CHAIR", 10, 10)
    assert batch.can_allocate(line)

def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch("batch-001", "RED-CHAIR", 10, eta=None)
    line = OrderLine("order-123", "YELLOW-SOFA", 2)
    assert batch.can_allocate(line) is False

def test_can_only_deallocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line("RED-CHAIR", 20, 2)
    batch.deallocate(unallocated_line)
    assert batch.available_quantity == 20

def test_allocation_is_idempotent():
    batch, line = make_batch_and_line("RED-CHAIR", 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18
