"""
Test suite to verify all backend API endpoints
Chạy: python test_api.py
"""
import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("Testing Backend APIs...")

    # 1. Root
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.text}"
    print(" Root API: OK")

    # 2. Login as admin
    login_res = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200, f"Login admin failed: {login_res.text}"
    admin_token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(" Login Manager: OK")

    # 3. Login as staff
    login_staff = client.post("/api/auth/login", data={"username": "nhanvien", "password": "nv123"})
    assert login_staff.status_code == 200, f"Login staff failed: {login_staff.text}"
    staff_token = login_staff.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    print(" Login Staff: OK")

    # 4. Categories & Suppliers & Products
    cat_res = client.get("/api/categories/", headers=admin_headers)
    assert cat_res.status_code == 200 and len(cat_res.json()) >= 5
    print(f" Categories list: {len(cat_res.json())} items - OK")

    supp_res = client.get("/api/suppliers/", headers=admin_headers)
    assert supp_res.status_code == 200 and len(supp_res.json()) >= 3
    print(f" Suppliers list: {len(supp_res.json())} items - OK")

    prod_res = client.get("/api/products/", headers=admin_headers)
    assert prod_res.status_code == 200 and len(prod_res.json()) >= 20
    print(f" Products list: {len(prod_res.json())} items - OK")

    # 5. Inventory & Dashboard & Alerts
    dash_res = client.get("/api/inventory/dashboard", headers=admin_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    print(f" Dashboard: {dash_data} - OK")

    alert_res = client.get("/api/inventory/alerts", headers=admin_headers)
    assert alert_res.status_code == 200
    print(f" Low stock alerts: {len(alert_res.json())} products below threshold - OK")

    # 6. AI Analysis
    ai_res = client.post("/api/proposals/ai-analyze", headers=staff_headers)
    assert ai_res.status_code == 200
    ai_suggestions = ai_res.json()
    assert len(ai_suggestions) > 0, "AI returned no suggestions!"
    print(f" AI Analysis: Generated {len(ai_suggestions)} replenish suggestions - OK")
    print(f"   Top suggestion: {ai_suggestions[0]['product_name']} | Q={ai_suggestions[0]['suggested_quantity']} | {ai_suggestions[0]['reason']}")

    # 7. Workflow: Create Proposal from AI suggestion -> Approve as Manager -> Complete
    first_sug = ai_suggestions[0]
    create_prop_res = client.post("/api/proposals/", json={
        "notes": "Đề xuất kiểm thử tự động",
        "ai_generated": True,
        "items": [{
            "product_id": first_sug["product_id"],
            "current_stock": first_sug["current_stock"],
            "suggested_quantity": first_sug["suggested_quantity"],
            "reason": first_sug["reason"],
            "priority": first_sug["priority"],
            "daily_consumption": first_sug["daily_consumption"]
        }]
    }, headers=staff_headers)
    assert create_prop_res.status_code == 201
    prop_data = create_prop_res.json()
    prop_id = prop_data["id"]
    print(f" Proposal created: Code {prop_data['code']} - Status: {prop_data['status']} - OK")

    # Approve as Manager
    approve_res = client.put(f"/api/proposals/{prop_id}/approve", json={"comment": "Duyệt qua test_api"}, headers=admin_headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"
    print(" Proposal Approved by Manager - OK")

    # Start progress as Staff
    start_res = client.put(f"/api/proposals/{prop_id}/start", headers=staff_headers)
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "IN_PROGRESS"
    print(" Proposal Started by Staff (IN_PROGRESS) - OK")

    # Complete as Staff
    comp_res = client.put(f"/api/proposals/{prop_id}/complete", headers=staff_headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"
    print(" Proposal Completed (Auto Import Order Created & Stock Updated) - OK")

    # 8. Reports
    rep_imp = client.get("/api/reports/imports", headers=admin_headers)
    assert rep_imp.status_code == 200
    print(f" Import report: {rep_imp.json()['total_orders']} orders, {rep_imp.json()['grand_total_amount']} VND - OK")

    rep_exp = client.get("/api/reports/exports", headers=admin_headers)
    assert rep_exp.status_code == 200
    print(f" Export report: {rep_exp.json()['total_orders']} orders - OK")

    rep_inv = client.get("/api/reports/inventory-summary", headers=admin_headers)
    assert rep_inv.status_code == 200
    print(f" Inventory summary: {rep_inv.json()['total_sku']} SKUs, Total Value: {rep_inv.json()['total_value']} VND - OK")

    # 9. Exports Validation (Check duplicate items & overstock prevention)
    # 9a. Duplicate products in export
    dup_exp = client.post("/api/exports/", json={
        "reason": "Tiêu thụ",
        "notes": "Test trùng lặp",
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 1, "quantity": 3}
        ]
    }, headers=staff_headers)
    assert dup_exp.status_code == 400, f"Expected 400 on duplicate export items, got {dup_exp.status_code}"
    print(" Export duplicate items prevented (400 Bad Request) - OK")

    # 9b. Exceeding current stock
    over_exp = client.post("/api/exports/", json={
        "reason": "Tiêu thụ",
        "notes": "Test xuất vượt tồn",
        "items": [
            {"product_id": 1, "quantity": 999999}
        ]
    }, headers=staff_headers)
    assert over_exp.status_code == 400, f"Expected 400 on overstock export, got {over_exp.status_code}"
    print(" Export overstock prevented (400 Bad Request) - OK")

    print("\nALL 9 BACKEND TESTS PASSED SUCCESSFULLY! ")

if __name__ == "__main__":
    run_tests()
