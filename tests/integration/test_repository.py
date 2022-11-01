import pytest

from domain import model
from adapters import repository


def insert_order_line(session) -> str:
    """Helper to insert an order line and return the id defined by the database"""
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty)"
        ' VALUES ("order1", "YELLOW-CHAIR", 12)'
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="YELLOW-CHAIR"),
    )
    return orderline_id

def insert_batch(session, batch_id) -> str:
    """Helper to insert a batch and return the id defined by the database"""
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        ' VALUES (:batch_id, "YELLOW-CHAIR", 100, null)',
        dict(batch_id=batch_id),
    )
    [[batch_id]] = session.execute(
        "SELECT id FROM batches WHERE reference=:batch_id AND sku='YELLOW-CHAIR'",
        dict(batch_id=batch_id),
    )
    return batch_id

def insert_allocation(session, orderline_id, batch_id) -> None:
    """Helper to insert allocation"""
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id)"
        ' VALUES (:orderline_id, :batch_id)',
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )


def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "YELLOW-CHAIR", 100, eta=None)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(
        "SELECT reference, sku, _purchased_quantity, eta FROM 'batches'"
    )
    assert list(rows) == [("batch1", "YELLOW-CHAIR", 100, None)]

def test_respository_can_retrieve_a_batch_with_allocation(session):
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, "batch1")
    insert_batch(session, "batch2")
    insert_allocation(session, orderline_id, batch1_id)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get("batch1")

    expected = model.Batch("batch1", "YELLOW-CHAIR", 100, None)
    assert retrieved == expected # compares reference
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        model.OrderLine("order1", "YELLOW-CHAIR", 12)
    }
