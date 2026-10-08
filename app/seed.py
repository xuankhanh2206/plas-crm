import json
from pathlib import Path
from .db import engine, SessionLocal, Base
from .models import Store, Product, Inventory, User

def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(Store).count():
            db.add_all([
                Store(code="PNT", name="Phạm Ngọc Thạch"),
                Store(code="NLB", name="Nguyễn Lương Bằng"),
                Store(code="HT", name="HT / kho chưa xác định"),
            ])
            db.commit()
        stores = {s.code: s for s in db.query(Store).all()}
        if not db.query(User).count():
            db.add_all([
                User(username="admin", full_name="PLAS Administrator", role="SUPER_ADMIN", password_hash="CHANGE_ME"),
                User(username="sales_pnt", full_name="Nhân viên PNT", role="SALES", password_hash="CHANGE_ME"),
                User(username="sales_nlb", full_name="Nhân viên NLB", role="SALES", password_hash="CHANGE_ME"),
            ])
            db.commit()
        seed_path = Path(__file__).resolve().parent.parent / "data" / "inventory_seed.json"
        items = json.loads(seed_path.read_text(encoding="utf-8"))
        if db.query(Product).count() == 0:
            for x in items:
                p = Product(
                    sku=x["sku"], source_stt=x["source_stt"], name=x["name"],
                    category=x["category"], origin=x["origin"], brand=x["brand"],
                    technique=x["technique"], shape=x["shape"], color=x["color"],
                    manufacturer_code=x["manufacturer_code"], size=x["size"],
                    collection=x["collection"], unit=x["unit"],
                    cost_price=x["cost_price"], list_price=x["list_price"],
                    abc_class=x["abc_class"], status=x["status"],
                    note=x["note"] or x["handling_note"]
                )
                db.add(p)
                db.flush()
                for code, qty in x["inventory"].items():
                    if code in stores:
                        db.add(Inventory(product_id=p.id, store_id=stores[code].id, quantity=qty))
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    run()
