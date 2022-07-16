import abc
from operator import mod
from typing import Set

from sqlalchemy.orm import Session

import model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError

class SqlRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, batch) -> None:
        """
        1) Add batch and get id in batches table
            -> If batch already exists, then just update: need to add this bit
        2) Add order_lines allocated to batch and get id from alllocated table
        3) Add record to allocations table using previous ids

        1 - check if a batch in batches exists with reference
        2 - if the batch exists, we need to perform some update
        3 - otherwise...
        4 - insert batch into batches + query to get the id (pk) of the batch
        5 - insert order line into order lines + query to get order line ids that have been allocated to the given batch
        6 - insert the order line id and batch id into allocations intermediate table
        """
        # Insert batch into `batches` and get id
        batch_row = self.session.execute(
            "SELECT id FROM batches WHERE reference = :reference",
            dict(reference=batch.reference),
        ).fetchone()

        if not batch_row:  # have to convert to list for conditional to work
            self.session.execute(
                "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES "
                '(:reference, :sku, :_purchased_quantity, :eta)',
                dict(
                    reference=batch.reference,
                    sku=batch.sku,
                    _purchased_quantity=batch._purchased_quantity,
                    eta=batch.eta,
                ),
            )
            # can use this syntax since guaranteed to have a batch_id exist
            [[batch_id]] = self.session.execute(
                "SELECT id FROM batches WHERE reference = :reference",
                dict(reference=batch.reference),
            )

            # Insert order line that has been allocated to the batch
            for line in batch._allocations:
                self.session.execute(
                    "INSERT INTO order_lines (sku, qty, orderid) VALUES "
                    '(:sku, :qty, :orderid)',
                    dict(sku=line.sku, qty=line.qty, orderid=line.orderid)
                )
            # Get order line ids of those just inserted
            orderline_rows = self.session.execute(
                "SELECT id FROM order_lines WHERE orderid in (:orderids)",
                dict(orderids=", ".join(map(lambda l: l.orderid, batch._allocations))),
            ).mappings().fetchall()  # mappings converts row to dict

            # Insert allocations associated with batch
            for row in orderline_rows:
                orderline_id = row["id"]
                self.session.execute(
                    "INSERT INTO allocations (orderline_id, batch_id) VALUES "
                    '(:orderline_id, :batch_id)',
                    dict(orderline_id=orderline_id, batch_id=batch_id),
                )

        else:
            # get order_id for those order lines already allocated to a batch
            orderlines_rows = self.session.execute(
                """
                SELECT
                    ol.orderid,
                    ol.sku,
                    ol.qty
                FROM
                    order_lines ol
                LEFT JOIN
                    allocations a
                ON
                    ol.id = a.orderline_id
                LEFT JOIN
                    batches b
                ON
                    a.batch_id = b.id
                WHERE
                    b.reference = :reference
                """,
                dict(reference=batch.reference)
            ).mappings().fetchall()

            orderlines = [model.OrderLine(**line) for line in orderlines_rows]
            lines_to_allocate = batch._allocations.difference(orderlines)
            
            for line in lines_to_allocate:
                self.session.execute(
                    "INSERT INTO order_lines (sku, qty, orderid) VALUES "
                    '(:sku, :qty, :orderid)',
                    dict(sku=line.sku, qty=line.qty, orderid=line.orderid)
                )
            # Get order line ids of those just inserted
            orderline_rows = self.session.execute(
                "SELECT id FROM order_lines WHERE orderid in (:orderids)",
                dict(orderids=", ".join(map(lambda l: l.orderid, lines_to_allocate))),
            ).mappings().fetchall()  # mappings converts row to dict
            # Insert allocations associated with batch
            [batch_id] = batch_row
            for row in orderline_rows:
                orderline_id = row["id"]
                self.session.execute(
                    "INSERT INTO allocations (orderline_id, batch_id) VALUES "
                    '(:orderline_id, :batch_id)',
                    dict(orderline_id=orderline_id, batch_id=batch_id),
                )
            

    def get(self, reference: str) -> model.Batch:
        # Get batch corresponding to reference
        [b] = self.session.execute(
            "SELECT id, reference, sku, _purchased_quantity, eta FROM batches WHERE reference=:reference",
            dict(reference=reference),
        )
        batch = model.Batch(b.reference, b.sku, b._purchased_quantity, b.eta)

        # Get order lines that have been allocated to that batch
        # !!! NEED TO READ FROM BATCHES FIRST!!!! OTHERWISE THOSE WITHOUT ALLOCATIONS WILL BE EXCLUDED
        ols = self.session.execute(
            "SELECT ol.sku, ol.qty, ol.orderid FROM allocations a LEFT JOIN order_lines ol ON a.orderline_id = ol.id WHERE a.batch_id=:batch_id",
            dict(batch_id=b.id),
        )
        order_lines = [model.OrderLine(line.orderid, line.sku, line.qty) for line in ols]

        # Allocate all order lines to batch
        for line in order_lines:
            batch.allocate(line)

        return batch


    def list(self) -> Set[model.Batch]:
        """
        for each batch in batches table:
            1 - construct batch object
            2 - construct allocated order lines
            3 - allocate those order lines
        
        """
        # get all batches in the batches tables: alias to match Batch constructor
        rows = self.session.execute(
            """
            SELECT
                reference as ref,
                sku,
                eta,
                _purchased_quantity as qty
            FROM
                batches
            """
        ).mappings().fetchall()

        # create Batch objects from query result
        batches = [model.Batch(**batch) for batch in rows]
        
        # for each batch, fetch all order lines allocated, instantiate and allocate
        for batch in batches:
            rows = self.session.execute(
                """
                SELECT
                    ol.orderid,
                    ol.sku,
                    ol.qty
                FROM
                    batches b
                LEFT JOIN
                    allocations a 
                ON
                    b.id = a.batch_id
                LEFT JOIN
                    order_lines ol
                ON
                    a.orderline_id = ol.id
                WHERE
                    b.reference = :reference
                """,
                dict(reference=batch.reference),
            )

            order_lines = [model.OrderLine(**line) for line in rows]

            for line in order_lines:
                batch.allocate(line)

        return batches
