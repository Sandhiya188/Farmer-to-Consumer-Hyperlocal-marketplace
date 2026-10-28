# 🌾 FarmConnect — Direct Farmer-to-Customer Marketplace

A complete, full-stack **Django** web application implementing direct farm-to-table pre-ordering with **SQLite3**, **HTML5/CSS3/JavaScript**, **OTP Verification**, and **Razorpay Test Mode**.

---

## 🗺️ Complete Workflow Implemented

```text
START
  ↓
User Registration (with 6-Digit OTP Section)
  ↓
  ├──👨‍🌾 FARMER
  │    ↓
  │  Farmer Login
  │    ↓
  │  Add Fresh Harvest (Vegetable / Fruit, Price + Stock Quantity)
  │    ↓
  │  Product Listed (Stock Available)
  │    ↓
  │  Farmer Receives Order Notification
  │    ↓
  │  Farmer Prepares Order (Update Status)
  │    ↓
  │  Ready for Collection / Delivery (Update Status)
  │    ↓
  └──🛒 CUSTOMER
       ↓
     Customer Login
       ↓
     Select Location / View Nearby Farmers
       ↓
     Browse Fresh Products & Check Stock Availability
       ↓
     Select Quantity & Add to Cart
       ↓
     JavaScript Dynamically Calculates Total Amount & Subtotals
       ↓
     💳 Choose Payment Method:
       ├── Cash on Delivery (COD) / Pay on Spot
       └── Online Payment (Razorpay Test Mode)
       ↓
     Place Pre-Order
       ↓
     Django Atomically Validates Stock Quantity:
       ├── If Stock Available:
       │     ✓ Order Confirmed (Save payment status)
       │     ✓ Reduce Stock Quantity
       │     ✓ Farmer Gets Order in Dashboard
       └── If Stock Not Available:
             ✗ Show "Out of Stock" Error & Prevent Order
       ↓
     Customer Receives Order (END)
```

---

## 🚀 Quick Start Guide

### 1. Open Terminal & Navigate to Project
```powershell
cd C:\Users\ELCOT\.gemini\antigravity\scratch\farm_connect
```

*(Tip: In Antigravity or your IDE, set `C:\Users\ELCOT\.gemini\antigravity\scratch\farm_connect` as your active workspace folder).*

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run Database Migrations (SQLite3)
```powershell
python manage.py makemigrations core
python manage.py migrate
```

### 5. Seed Realistic Test Data (Farmers, Produce & Customer)
```powershell
python manage.py seed_data
```
This automatically sets up:
* **Admin**: `username: admin`, `password: admin123`
* **Farmer 1 (Pune)**: `username: farmer_ramesh`, `password: password123`
  - Fresh Tomatoes, Alphonso Mangoes, Hydroponic Spinach
* **Farmer 2 (Nashik)**: `username: farmer_suresh`, `password: password123`
  - Nashik Red Onions, Black Grapes, Capsicum
* **Customer**: `username: customer_anita`, `password: password123`

### 6. Start the Local Server
```powershell
python manage.py runserver
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

---

## 🔑 Key Features & Architecture

### 1. 📲 OTP Verification Section
* **Registration**: When a user registers as Farmer or Customer, a 6-digit OTP is generated.
* **Development Convenience**: In development/test mode, the generated OTP is automatically rendered on the verification screen and in the Django flash message banner.
* **Expiry**: OTP tokens expire after 10 minutes and support a 1-click **Resend OTP** flow.

### 2. ⚡ Real-Time JavaScript Calculations
* **Interactive Cart**: `static/js/main.js` recalculates item subtotals (`price * quantity`) and grand totals dynamically without reloading the page.
* **AJAX Synchronization**: Changes are synced asynchronously with the Django backend.
* **Live Product Estimator**: Changes on product detail pages dynamically calculate `Total: ₹...`.

### 3. 🔒 Robust Django Stock Validation
* **Atomic Concurrency**: Validations in `checkout_view` use `transaction.atomic()` with `select_for_update()`.
* **Stock Deductions**: If stock is available, quantities are reduced from the SQLite database.
* **Out of Stock Guard**: If another user orders the last units simultaneously, an immediate "Out of Stock" notification is shown, preventing overselling.

### 4. 💳 Payment Method Integration
* **Cash on Delivery (COD) / Pay on Spot**: Order is created with `payment_status = 'pending'` and marked completed upon delivery.
* **Razorpay Test Mode**: Integrated via Razorpay's JavaScript SDK modal, complete with mock-mode offline simulation support.

### 5. 👨‍🌾 Farmer Order Management
* Farmers view incoming orders containing their produce.
* Status advancement buttons:
  - `Order Placed` ➔ `Farmer Prepares Order` ➔ `Ready for Collection/Delivery` ➔ `Customer Received (Completed)`.
* Customers view an interactive visual progress tracker on their order page.
