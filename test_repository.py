from datetime import (
    date,
    timedelta,
)
import pytest

import model
import respository


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def insert_order_line(session, line: model.OrderLine) -> str:
    """Helper to insert an order line and return the id defined by the database"""
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty)"
        ' VALUES (:orderid, :sku, :qty)',
        dict(orderid=line.orderid, sku=line.sku, qty=line.qty)
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid=line.orderid, sku=line.sku),
    )

    return orderline_id

def insert_batch(session, batch: model.Batch) -> str:
    """Helper to insert a batch and return the id defined by the database"""
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        ' VALUES (:reference, :sku, :qty, :eta)',
        dict(reference=batch.reference, sku=batch.sku, qty=batch._purchased_quantity, eta=batch.eta or "null"),
    )
    [[batch_id]] = session.execute(
        "SELECT id FROM batches WHERE reference=:reference AND sku=:sku",
        dict(reference=batch.reference, sku=batch.sku),
    )
    return batch_id

def insert_allocation(session, orderline_id, batch_id) -> None:
    """Helper to insert allocation"""
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id)"
        ' VALUES (:orderline_id, :batch_id)',
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )

# @pytest.mark.skip
def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "YELLOW-CHAIR", 100, eta=None)

    repo = respository.SqlRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(
        "SELECT reference, sku, _purchased_quantity, eta FROM 'batches'"
    )
    assert list(rows) == [("batch1", "YELLOW-CHAIR", 100, None)]

# @pytest.mark.skip
def test_respository_can_retrieve_a_batch_with_allocation(session):
    ol1 = model.OrderLine("orderid-1", "YELLOW-CHAIR", 10)
    ol1_id = insert_order_line(session, line=ol1)

    ol2 = model.OrderLine("orderid-2", "YELLOW-CHAIR", 20)
    ol2_id = insert_order_line(session, line=ol2)

    # 2 allocations
    b1 = model.Batch("batchref-1", "YELLOW-CHAIR", 100, None)
    b1_id = insert_batch(session, b1)

    # no allocations
    b2 = model.Batch("batchref-2", "YELLOW-CHAIR", 100, tomorrow)
    insert_batch(session, b2)
    
    insert_allocation(session, ol1_id, b1_id)
    insert_allocation(session, ol2_id, b1_id)

    repo = respository.SqlRepository(session)
    retrieved = repo.get("batchref-1")

    expected = model.Batch("batchref-1", "YELLOW-CHAIR", 100, None)
    assert retrieved == expected # __eq__ compares reference: custom dunder defined in class
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        model.OrderLine("orderid-1", "YELLOW-CHAIR", 10),
        model.OrderLine("orderid-2", "YELLOW-CHAIR", 20),
    }

def get_allocations(session, batchid: str):
    rows = list(
        session.execute(
            """
            SELECT
                orderid
            FROM
                allocations a
            JOIN
                order_lines ol ON a.orderline_id = ol.id
            JOIN
                batches b ON a.batch_id = b.id
            WHERE
                b.reference = :batchid
            """,
            dict(batchid=batchid)
        )
    )
    return {row[0] for row in rows}


def test_updating_a_batch(session):
    ol1 = model.OrderLine("orderid-1", "RED-CHAIR", 10)
    ol2 = model.OrderLine("orderid-2", "RED-CHAIR", 20)

    b = model.Batch("batchref-1", "RED-CHAIR", 100, None)

    repo = respository.SqlRepository(session)

    b.allocate(ol1)
    repo.add(b)
    session.commit()

    b.allocate(ol2)
    repo.add(b)
    session.commit()

    assert get_allocations(session, "batchref-1") == {"orderid-1", "orderid-2"}

def test_repository_can_retrieve_all_batches(session):
    # create order_line, insert into db and get id
    ol1 = model.OrderLine("orderid-1", "YELLOW-CHAIR", 10)
    ol1_id = insert_order_line(session, line=ol1)

    # # create another order_line, insert into db and get id
    ol2 = model.OrderLine("orderid-2", "YELLOW-CHAIR", 20)
    ol2_id = insert_order_line(session, line=ol2)

    # create batch, allocate both order_lines above to this batch, both in db and deserialised objects
    b1 = model.Batch("batchref-1", "YELLOW-CHAIR", 100, None)
    b1_id = insert_batch(session, b1)
    insert_allocation(session, ol1_id, b1_id)
    insert_allocation(session, ol2_id, b1_id)
    b1.allocate(ol1)
    b1.allocate(ol2)

    # create batch and do not allocate any order_lines to it
    b2 = model.Batch("batchref-2", "YELLOW-CHAIR", 100, tomorrow)
    insert_batch(session, b2)
    
    # get batches repo
    repo = respository.SqlRepository(session)

    # SUT: fetch all batches from the batches repository
    batches = repo.list()
    
    expected = [b1, b2]
    assert batches == expected
    # first batch: correctly allocated order_lines
    assert b1.sku == "YELLOW-CHAIR"
    assert b1._purchased_quantity == 100
    assert b1._allocations == {
        model.OrderLine("orderid-1", "YELLOW-CHAIR", 10),
        model.OrderLine("orderid-2", "YELLOW-CHAIR", 20),
    }
    # second batch: no allocations
    assert b2.sku == "YELLOW-CHAIR"
    assert b2._purchased_quantity == 100
    assert b2._allocations == set()
