from dataclasses import dataclass
from datetime import date
from typing import List
from typing import Optional
from typing import Set


@dataclass(unsafe_hash=True)
class OrderLine:
    """Represents Order Line entity within an Order entity"""
    orderid: str
    sku: str
    qty: int

class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: Set[OrderLine] = set() # sets give us idempotent allocations for free

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def allocate(self, line: OrderLine) -> None:
        """Allocate an OrderLine to a Batch"""
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)
        
    def can_allocate(self, line: OrderLine) -> bool:
        """Helper function for checking SKUs match and enough available quantity"""
        return self.sku == line.sku and self.available_quantity >= line.qty

    def __eq__(self, other: object) -> bool:
        """Special method required to define referential equality of two Batch entities."""
        if not isinstance(other, Batch): # check comparison object is of type Batch
            return False
        return self.reference == other.reference # referential equality

    def __gt__(self, other: object) -> bool:
        """Special method required to define ordering behaviour of batches."""
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __hash__(self) -> int:
        return hash(self.reference)


class Product:
    """Aggregate for allocating order lines to batches."""
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")


class OutOfStock(Exception):
    ...
