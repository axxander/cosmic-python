from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)
from sqlalchemy.orm import (
    relationship,
    registry,
)

from domain import model


metadata = MetaData()

# Table for representing Order Lines
order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
)

# Table for representing Batches
batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("_purchased_quantity", Integer, nullable=False),
    Column("eta", Date, nullable=True),
)

# Table for respresenting OrderLine Id <=0---0=> (m-to-m) Batch Id (intermediate table)
allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement= True),
    Column("orderline_id", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id")),
)


def start_mappers():
    """
    Defines mapping of Python Domain Model -> Database model
    """
    mapper_registry = registry()
    lines_mapper = mapper_registry.map_imperatively(model.OrderLine, order_lines)
    # Batches related to Order Line via Allocations Intermediate
    mapper_registry.map_imperatively(
        model.Batch,
        batches,
        properties={
            "_allocations": relationship(
                lines_mapper,
                secondary=allocations, # intermediate table
                collection_class=set, # allocations are idempotent and cannot be repeated
            )
        }
    )
