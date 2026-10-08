from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from .db import Base, engine, get_db
from .models import Store, Product, Inventory, Customer, LoyaltyTransaction, Order, OrderItem, AuditLog
from .seed import run as seed_run
from pydantic import BaseModel
from typing import Optional
import uuid, os, re

app = FastAPI(title="PLAS CRM / POS / Loyalty", version="1.0.0")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup():
    seed_run()

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    product_count = db.query(Product).count()
    customer_count = db.query(Customer).count()
    order_count = db.query(Order).count()
    inventory_units = db.query(func.coalesce(func.sum(Inventory.quantity), 0)).scalar() or 0
    inventory_cost = db.query(func.coalesce(func.sum(Inventory.quantity * Product.cost_price), 0)).join(Product).scalar() or 0
    inventory_retail = db.query(func.coalesce(func.sum(Inventory.quantity * Product.list_price), 0)).join(Product).scalar() or 0
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "product_count": product_count, "customer_count": customer_count,
        "order_count": order_count, "inventory_units": inventory_units,
        "inventory_cost": int(inventory_cost), "inventory_retail": int(inventory_retail)
    })

@app.get("/api/products")
def products(q: Optional[str]=None, store: Optional[str]=None, db: Session=Depends(get_db)):
    query = db.query(Product)
    if q:
        like=f"%{q}%"
        query=query.filter((Product.name.ilike(like)) | (Product.sku.ilike(like)))
    rows=query.order_by(Product.source_stt).all()
    out=[]
    for p in rows:
        inv = {s.code: 0 for s in db.query(Store).all()}
        for i in db.query(Inventory).filter(Inventory.product_id==p.id).all():
            inv[i.store.code]=i.quantity
        if store and inv.get(store,0) == 0:
            continue
        out.append({
            "id":p.id,"sku":p.sku or f"PLAS-{p.source_stt:04d}","name":p.name,
            "category":p.category,"brand":p.brand,"list_price":p.list_price,
            "cost_price":p.cost_price,"abc":p.abc_class,"status":p.status,"inventory":inv
        })
    return out

@app.get("/api/customers")
def customers(q: Optional[str]=None, db: Session=Depends(get_db)):
    query=db.query(Customer)
    if q:
        like=f"%{q}%"
        query=query.filter((Customer.phone.ilike(like)) | (Customer.name.ilike(like)))
    rows=query.order_by(Customer.id.desc()).limit(100).all()
    result=[]
    for c in rows:
        points=db.query(func.coalesce(func.sum(LoyaltyTransaction.points),0)).filter(LoyaltyTransaction.customer_id==c.id).scalar() or 0
        total=db.query(func.coalesce(func.sum(Order.total_paid),0)).filter(Order.customer_id==c.id, Order.status=="COMPLETED").scalar() or 0
        result.append({"id":c.id,"phone":c.phone,"name":c.name,"source":c.source,"points":int(points),"total_spend":int(total)})
    return result

class CustomerIn(BaseModel):
    phone: str
    name: str
    source: str = "STORE"
    email: Optional[str] = None
    note: Optional[str] = None

@app.post("/api/customers")
def create_customer(payload: CustomerIn, db: Session=Depends(get_db)):
    phone=re.sub(r"\D","",payload.phone)
    if not phone: raise HTTPException(400,"Số điện thoại không hợp lệ")
    if db.query(Customer).filter(Customer.phone==phone).first():
        raise HTTPException(409,"Số điện thoại đã tồn tại")
    c=Customer(phone=phone,name=payload.name.strip(),source=payload.source,email=payload.email,note=payload.note)
    db.add(c); db.commit(); db.refresh(c)
    return {"id":c.id,"phone":c.phone,"name":c.name}

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int
    selling_price: Optional[int] = None

class OrderIn(BaseModel):
    phone: Optional[str] = None
    store_code: str
    items: list[OrderItemIn]
    points_used: int = 0
    discount: int = 0
    payment_method: str = "CASH"

@app.post("/api/orders")
def create_order(payload: OrderIn, db: Session=Depends(get_db)):
    store=db.query(Store).filter(Store.code==payload.store_code).first()
    if not store or store.code=="HT":
        raise HTTPException(400,"Chỉ PNT/NLB được phép bán hàng")
    customer=None
    if payload.phone:
        phone=re.sub(r"\D","",payload.phone)
        customer=db.query(Customer).filter(Customer.phone==phone).first()
        if not customer:
            raise HTTPException(400,"Khách chưa tồn tại. Hãy tạo hồ sơ khách trước.")
    subtotal=0
    prepared=[]
    for item in payload.items:
        if item.quantity <= 0: raise HTTPException(400,"Số lượng phải > 0")
        p=db.get(Product,item.product_id)
        if not p: raise HTTPException(404,f"Không tìm thấy sản phẩm {item.product_id}")
        inv=db.query(Inventory).filter(Inventory.product_id==p.id, Inventory.store_id==store.id).with_for_update().first()
        if not inv or inv.quantity < item.quantity:
            raise HTTPException(409,f"Không đủ tồn kho tại {store.code}: {p.name}")
        price=p.list_price if item.selling_price is None else item.selling_price
        if price < 0: raise HTTPException(400,"Giá bán không hợp lệ")
        line=price*item.quantity
        subtotal += line
        prepared.append((p,inv,item,price,line))
    # Loyalty is based on LIST PRICE snapshot, not discounted selling price.
    eligible_points=sum(p.list_price*item.quantity for p,inv,item,price,line in prepared)//100
    if payload.points_used < 0: raise HTTPException(400,"Điểm sử dụng không hợp lệ")
    if payload.points_used and payload.discount:
        raise HTTPException(400,"Không được dùng điểm đồng thời với voucher/khuyến mãi")
    if customer:
        current=db.query(func.coalesce(func.sum(LoyaltyTransaction.points),0)).filter(LoyaltyTransaction.customer_id==customer.id).scalar() or 0
        if payload.points_used > current: raise HTTPException(409,"Khách không đủ điểm")
    total=max(0, subtotal-payload.discount-payload.points_used)
    order_no="PLAS-"+uuid.uuid4().hex[:10].upper()
    order=Order(order_no=order_no,customer_id=customer.id if customer else None,store_id=store.id,
                subtotal=subtotal,discount=payload.discount,points_used=payload.points_used,total_paid=total,status="COMPLETED")
    db.add(order); db.flush()
    for p,inv,item,price,line in prepared:
        db.add(OrderItem(order_id=order.id,product_id=p.id,quantity=item.quantity,
                         list_price_snapshot=p.list_price,selling_price=price,line_total=line))
        inv.quantity -= item.quantity
    if customer:
        if payload.points_used:
            db.add(LoyaltyTransaction(customer_id=customer.id,points=-payload.points_used,type="REDEEM",reference=order_no,reason="Sử dụng điểm tại POS"))
        if eligible_points:
            db.add(LoyaltyTransaction(customer_id=customer.id,points=eligible_points,type="EARN",reference=order_no,reason="1% giá bán niêm yết"))
    db.add(AuditLog(action="CREATE_ORDER",actor="POS",entity_type="ORDER",entity_id=order_no,
                    detail=f"store={store.code}; subtotal={subtotal}; points_earned={eligible_points}; points_used={payload.points_used}"))
    db.commit()
    return {"order_no":order_no,"subtotal":subtotal,"discount":payload.discount,"points_used":payload.points_used,
            "total_paid":total,"points_earned":eligible_points}

@app.get("/api/summary")
def summary(db: Session=Depends(get_db)):
    stores={}
    for s in db.query(Store).filter(Store.code.in_(["PNT","NLB"])).all():
        units=db.query(func.coalesce(func.sum(Inventory.quantity),0)).filter(Inventory.store_id==s.id).scalar() or 0
        value=db.query(func.coalesce(func.sum(Inventory.quantity*Product.cost_price),0)).join(Product).filter(Inventory.store_id==s.id).scalar() or 0
        retail=db.query(func.coalesce(func.sum(Inventory.quantity*Product.list_price),0)).join(Product).filter(Inventory.store_id==s.id).scalar() or 0
        stores[s.code]={"name":s.name,"units":int(units),"cost_value":int(value),"retail_value":int(retail)}
    return stores
