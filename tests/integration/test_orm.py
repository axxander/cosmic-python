from datetime import date

import pytest

from domain import model


def test_orderline_mapper_can_load_lines(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES "
        '("order1", "RED-CHAIR", 12),'
        '("order1", "RED-TABLE", 13),'
        '("order2", "BLUE-LIPSTICK", 14)'
    )
    expected = [
        model.OrderLine("order1", "RED-CHAIR", 12),
        model.OrderLine("order1", "RED-TABLE", 13),
        model.OrderLine("order2", "BLUE-LIPSTICK", 14),
    ]
    assert session.query(model.OrderLine).all() == expected

def test_orderline_mapper_can_save_lines(session):
    new_line = model.OrderLine("order1", "YELLOW-CHAIR", 12)
    session.add(new_line)
    session.commit()

    rows = list(session.execute("SELECT orderid, sku, qty FROM 'order_lines'"))
    assert rows == [("order1", "YELLOW-CHAIR", 12)]


def test_batches_mapper_can_load(session):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES "
        '("order-ref1", "RED-CHAIR", 12, NULL),'
        '("order-ref2", "RED-TABLE", 13, "2022-06-01"),'
        '("order-ref3", "BLUE-LIPSTICK", 14, "2022-06-10")'
    )
    expected = [
        model.Batch("order-ref1", "RED-CHAIR", 12, None),
        model.Batch("order-ref2", "RED-TABLE", 13, date(2022, 6, 1)),
        model.Batch("order-ref3", "BLUE-LIPSTICK", 14, date(2022, 6, 10)),
    ]
    assert session.query(model.Batch).all() == expected

def test_batches_mapper_can_save_batches(session):
    new_batch = model.Batch("order-ref1", "RED-CHAIR", 5, None)
    session.add(new_batch)
    session.commit()

    rows = list(session.execute("SELECT reference, sku, _purchased_quantity, eta FROM 'batches'"))
    assert rows == [("order-ref1", "RED-CHAIR", 5, None)]


def test_saving_allocations(session):
    batch = model.Batch("batch1", "sku1", 100, eta=None)
    line = model.OrderLine("order1", "sku1", 10)

    batch.allocate(line)
    session.add(batch)
    session.commit()

    rows = list(session.execute("SELECT orderline_id, batch_id FROM 'allocations'"))
    assert rows == [(batch.id, line.id)]

def test_retrieving_allocations(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES ('orderid1', 'sku1', 12)"
    )
    [[olid]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="orderid1", sku="sku1"),
    )

    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        ' VALUES ("batch1", "sku1", 100, null)'
    )
    [[bid]] = session.execute(
        "SELECT id FROM batches WHERE reference=:ref AND sku=:sku",
        dict(ref="batch1", sku="sku1"),
    )

    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id) VALUES (:olid, :bid)",
        dict(olid=olid, bid=bid),
    )

    batch = session.query(model.Batch).one()

    assert batch._allocations == {model.OrderLine("orderid1", "sku1", 12)}