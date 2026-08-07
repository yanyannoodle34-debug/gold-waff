"""Customer registration and lookup."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from ..deps import not_found
from ..models import Customer
from ..store import get_store

router = APIRouter(prefix="/customers", tags=["Customers"])


class CustomerIn(BaseModel):
    name: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""


@router.get("", response_model=List[Customer])
def list_customers() -> List[Customer]:
    return list(get_store().customers.values())


@router.post("", response_model=Customer, status_code=201)
def register_customer(body: CustomerIn) -> Customer:
    store = get_store()
    customer = Customer(id=store.next_id("CUS"), **body.model_dump())
    store.customers[customer.id] = customer
    store.log(f"[Customer] Registered {customer.name} ({customer.id})")
    return customer


@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: str) -> Customer:
    customer = get_store().customers.get(customer_id)
    if customer is None:
        raise not_found(f"Unknown customer: {customer_id}")
    return customer
