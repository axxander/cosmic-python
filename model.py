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


class OutOfStock(Exception):
    ...


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    """Allocate an Order Line given a list of Batches according to business rules
    * Allocated warehouse stock >> shipping stock
    * Allocate order line to batch with earliest ETA
    * Raise error if unable to allocate
    """
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"The SKU `{line.sku}` is out of stock")