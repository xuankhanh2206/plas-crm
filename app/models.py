from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .db import Base

class Store(Base):
    __tablename__ = "stores"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    source_stt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(300), index=True)
    category: Mapped[str | None] = mapped_column(String(120), index=True)
    origin: Mapped[str | None] = mapped_column(String(120))
    brand: Mapped[str | None] = mapped_column(String(150), index=True)
    technique: Mapped[str | None] = mapped_column(String(120))
    shape: Mapped[str | None] = mapped_column(String(120))
    color: Mapped[str | None] = mapped_column(String(120))
    manufacturer_code: Mapped[str | None] = mapped_column(String(120))
    size: Mapped[str | None] = mapped_column(String(80))
    collection: Mapped[str | None] = mapped_column(String(150))
    unit: Mapped[str] = mapped_column(String(30), default="Chiếc")
    cost_price: Mapped[int] = mapped_column(Integer, default=0)
    list_price: Mapped[int] = mapped_column(Integer, default=0)
    abc_class: Mapped[str | None] = mapped_column(String(2))
    status: Mapped[str] = mapped_column(String(50), default="Còn hàng")
    note: Mapped[str | None] = mapped_column(Text)

class Inventory(Base):
    __tablename__ = "inventory"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    product = relationship("Product")
    store = relationship("Store")

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(200))
    source: Mapped[str | None] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    points: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(30))
    reference: Mapped[str | None] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    subtotal: Mapped[int] = mapped_column(Integer, default=0)
    discount: Mapped[int] = mapped_column(Integer, default=0)
    points_used: Mapped[int] = mapped_column(Integer, default=0)
    total_paid: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    list_price_snapshot: Mapped[int] = mapped_column(Integer)
    selling_price: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[int] = mapped_column(Integer)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(80))
    actor: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(80))
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    role: Mapped[str] = mapped_column(String(30), default="SALES")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[str] = mapped_column(String(255), default="")

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    from_store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    to_store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(30))
    reference: Mapped[str | None] = mapped_column(String(100))
    actor: Mapped[str] = mapped_column(String(100))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CustomerInteraction(Base):
    __tablename__ = "customer_interactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    channel: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
