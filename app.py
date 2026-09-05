# =====================================================
# COREFIX TECHNOLOGIES
# FLASK BACKEND
# REPAIRS + PRODUCTS + IMAGES + ORDERS
# =====================================================

import hmac
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from database import (
    # Repairs
    create_database,
    add_repair,
    get_repair,
    get_all_repairs,
    update_repair_status,

    # Products
    add_product,
    get_all_products,
    get_product,
    update_product,
    delete_product,

    # Orders
    add_order,
    get_order,
    get_all_orders,
    update_order_status,
    delete_order,
)


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


# =====================================================
# FLASK APPLICATION
# =====================================================

app = Flask(__name__)


# =====================================================
# SECURITY / SESSION CONFIGURATION
# =====================================================

secret_key = os.getenv("SECRET_KEY", "").strip()

if not secret_key:
    # Safe for local development only. Set SECRET_KEY in .env / hosting
    # environment before deployment so sessions survive restarts.
    secret_key = secrets.token_hex(32)
    print(
        "WARNING: SECRET_KEY is not set. "
        "A temporary development key is being used."
    )

app.secret_key = secret_key

is_production = os.getenv("APP_ENV", "development").lower() == "production"

app.config.update(
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=is_production,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)


# =====================================================
# PRODUCT IMAGE UPLOAD CONFIGURATION
# =====================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "assets",
    "products",
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
}

ALLOWED_IMAGE_MIMETYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
}

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True,
)


# =====================================================
# DATABASE
# =====================================================

create_database()


# =====================================================
# HELPERS
# =====================================================

def json_error(message, status_code):
    return jsonify({
        "success": False,
        "message": message,
    }), status_code


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return json_error("Unauthorized.", 401)

        return function(*args, **kwargs)

    return wrapper


def allowed_file(filename):
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def generate_repair_id():
    while True:
        year = datetime.now().year
        random_number = secrets.randbelow(90000) + 10000
        repair_id = f"CF-{year}-{random_number}"

        if not get_repair(repair_id):
            return repair_id


def generate_order_id():
    while True:
        year = datetime.now().year

        # Eight random hexadecimal characters make newly generated order IDs
        # much harder to guess than a five-digit number.
        token = secrets.token_hex(4).upper()
        order_id = f"ORD-{year}-{token}"

        if not get_order(order_id):
            return order_id


def masked_name(name):
    name = str(name or "").strip()

    if not name:
        return ""

    words = name.split()
    masked_words = []

    for word in words:
        if len(word) <= 1:
            masked_words.append(word)
        else:
            masked_words.append(word[0] + "*" * (len(word) - 1))

    return " ".join(masked_words)


def masked_phone(phone):
    phone = str(phone or "").strip()

    if len(phone) <= 4:
        return "*" * len(phone)

    return "*" * (len(phone) - 4) + phone[-4:]


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# ADMIN PAGE
# =====================================================

@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    return render_template("admin.html")


# =====================================================
# ADMIN LOGIN
# =====================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"],
)
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin_username = os.getenv("ADMIN_USERNAME", "").strip()
        admin_password = os.getenv("ADMIN_PASSWORD", "")

        if not admin_username or not admin_password:
            error = "Admin credentials are not configured."
        else:
            username_ok = hmac.compare_digest(username, admin_username)
            password_ok = hmac.compare_digest(password, admin_password)

            if username_ok and password_ok:
                session.clear()
                session["admin_logged_in"] = True
                session.permanent = True

                return redirect(url_for("admin"))

            error = "Invalid username or password."

    return render_template(
        "admin_login.html",
        error=error,
    )


# =====================================================
# ADMIN LOGOUT
# =====================================================

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# =====================================================
# CUSTOMER - CREATE REPAIR REQUEST
# =====================================================

@app.route(
    "/api/repairs",
    methods=["POST"],
)
def create_repair():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return json_error("No repair information received.", 400)

        name = str(data.get("name", "")).strip()
        phone = str(data.get("phone", "")).strip()
        device = str(data.get("device", "")).strip()
        brand = str(data.get("brand", "")).strip()
        model = str(data.get("model", "")).strip()
        issue = str(data.get("issue", "")).strip()
        description = str(data.get("description", "")).strip()
        contact_method = str(data.get("contactMethod", "WhatsApp")).strip()

        required_fields = {
            "name": (name, "Please enter your name."),
            "phone": (phone, "Please enter your phone number."),
            "device": (device, "Please select your device type."),
            "brand": (brand, "Please select your device brand."),
            "model": (model, "Please enter your device model."),
            "issue": (issue, "Please select the device problem."),
            "description": (description, "Please describe the device problem."),
        }

        for _, (value, message) in required_fields.items():
            if not value:
                return json_error(message, 400)

        if not contact_method:
            contact_method = "WhatsApp"

        repair_id = generate_repair_id()

        add_repair(
            repair_id,
            name,
            phone,
            device,
            brand,
            model,
            issue,
            description,
            contact_method,
        )

        return jsonify({
            "success": True,
            "message": "Repair request submitted successfully.",
            "repairId": repair_id,
        }), 201

    except Exception as error:
        print("Create repair error:", error)
        return json_error(
            "Something went wrong while submitting the repair request.",
            500,
        )


# =====================================================
# CUSTOMER - TRACK REPAIR
# =====================================================

@app.route(
    "/api/repairs/<repair_id>",
    methods=["GET"],
)
def track_repair(repair_id):
    try:
        repair_id = repair_id.strip().upper()
        repair = get_repair(repair_id)

        if not repair:
            return json_error("Repair request not found.", 404)

        return jsonify({
            "success": True,
            "repair": {
                "repairId": repair["repair_id"],
                "device": repair["device"],
                "brand": repair["brand"],
                "model": repair["model"],
                "issue": repair["issue"],
                "status": repair["status"],
                "createdAt": repair["created_at"],
            },
        }), 200

    except Exception as error:
        print("Track repair error:", error)
        return json_error("Unable to track repair.", 500)


# =====================================================
# ADMIN - GET ALL REPAIRS
# =====================================================

@app.route(
    "/api/admin/repairs",
    methods=["GET"],
)
@admin_required
def admin_repairs():
    try:
        repairs = get_all_repairs()

        results = [
            {
                "repairId": repair["repair_id"],
                "name": repair["name"],
                "phone": repair["phone"],
                "device": repair["device"],
                "brand": repair["brand"],
                "model": repair["model"],
                "issue": repair["issue"],
                "description": repair["description"],
                "contactMethod": repair["contact_method"],
                "status": repair["status"],
                "createdAt": repair["created_at"],
            }
            for repair in repairs
        ]

        return jsonify({
            "success": True,
            "repairs": results,
        }), 200

    except Exception as error:
        print("Admin repairs error:", error)
        return json_error("Unable to load repair requests.", 500)


# =====================================================
# ADMIN - UPDATE REPAIR STATUS
# =====================================================

@app.route(
    "/api/admin/repairs/<repair_id>/status",
    methods=["PUT"],
)
@admin_required
def change_status(repair_id):
    try:
        repair_id = repair_id.strip().upper()
        repair = get_repair(repair_id)

        if not repair:
            return json_error("Repair request not found.", 404)

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return json_error("No status received.", 400)

        new_status = str(data.get("status", "")).strip()

        allowed_statuses = {
            "Request Received",
            "Device Inspection",
            "Repair In Progress",
            "Ready for Collection",
        }

        if new_status not in allowed_statuses:
            return json_error("Invalid repair status.", 400)

        update_repair_status(
            repair_id,
            new_status,
        )

        return jsonify({
            "success": True,
            "message": "Repair status updated successfully.",
            "repairId": repair_id,
            "status": new_status,
        }), 200

    except Exception as error:
        print("Status update error:", error)
        return json_error("Unable to update repair status.", 500)


# =====================================================
# PUBLIC - GET PRODUCTS
# =====================================================

@app.route(
    "/api/products",
    methods=["GET"],
)
def public_products():
    try:
        products = get_all_products()

        results = [
            {
                "id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "price": product["price"],
                "icon": product["icon"],
                "stockStatus": product["stock_status"],
                "image": product["image"] or "",
            }
            for product in products
        ]

        return jsonify({
            "success": True,
            "products": results,
        }), 200

    except Exception as error:
        print("Load products error:", error)
        return json_error("Unable to load products.", 500)


# =====================================================
# ADMIN - ADD PRODUCT
# =====================================================

@app.route(
    "/api/admin/products",
    methods=["POST"],
)
@admin_required
def admin_add_product():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return json_error("No product information received.", 400)

        name = str(data.get("name", "")).strip()
        description = str(data.get("description", "")).strip()
        icon = str(data.get("icon", "📦")).strip() or "📦"
        stock_status = str(data.get("stockStatus", "In Stock")).strip()
        image = str(data.get("image", "")).strip()

        try:
            price = int(data.get("price", 0))
        except (TypeError, ValueError):
            return json_error("Invalid product price.", 400)

        if not name:
            return json_error("Product name is required.", 400)

        if not description:
            return json_error("Product description is required.", 400)

        if price < 0:
            return json_error("Price cannot be negative.", 400)

        allowed_stock_statuses = {
            "In Stock",
            "Low Stock",
            "Out of Stock",
        }

        if stock_status not in allowed_stock_statuses:
            return json_error("Invalid stock status.", 400)

        add_product(
            name,
            description,
            price,
            icon,
            stock_status,
            image,
        )

        return jsonify({
            "success": True,
            "message": "Product added successfully.",
        }), 201

    except Exception as error:
        print("Add product error:", error)
        return json_error("Unable to add product.", 500)


# =====================================================
# ADMIN - UPDATE PRODUCT
# =====================================================

@app.route(
    "/api/admin/products/<int:product_id>",
    methods=["PUT"],
)
@admin_required
def admin_update_product(product_id):
    try:
        product = get_product(product_id)

        if not product:
            return json_error("Product not found.", 404)

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return json_error("No product information received.", 400)

        name = str(data.get("name", product["name"])).strip()
        description = str(
            data.get("description", product["description"])
        ).strip()
        icon = str(data.get("icon", product["icon"])).strip() or "📦"
        stock_status = str(
            data.get("stockStatus", product["stock_status"])
        ).strip()
        image = str(
            data.get("image", product["image"] or "")
        ).strip()

        try:
            price = int(data.get("price", product["price"]))
        except (TypeError, ValueError):
            return json_error("Invalid product price.", 400)

        if not name:
            return json_error("Product name is required.", 400)

        if not description:
            return json_error("Product description is required.", 400)

        if price < 0:
            return json_error("Price cannot be negative.", 400)

        allowed_stock_statuses = {
            "In Stock",
            "Low Stock",
            "Out of Stock",
        }

        if stock_status not in allowed_stock_statuses:
            return json_error("Invalid stock status.", 400)

        update_product(
            product_id,
            name,
            description,
            price,
            icon,
            stock_status,
            image,
        )

        return jsonify({
            "success": True,
            "message": "Product updated successfully.",
        }), 200

    except Exception as error:
        print("Update product error:", error)
        return json_error("Unable to update product.", 500)


# =====================================================
# ADMIN - DELETE PRODUCT
# =====================================================

@app.route(
    "/api/admin/products/<int:product_id>",
    methods=["DELETE"],
)
@admin_required
def admin_delete_product(product_id):
    try:
        product = get_product(product_id)

        if not product:
            return json_error("Product not found.", 404)

        delete_product(product_id)

        return jsonify({
            "success": True,
            "message": "Product deleted successfully.",
        }), 200

    except Exception as error:
        print("Delete product error:", error)
        return json_error("Unable to delete product.", 500)


# =====================================================
# ADMIN - UPLOAD PRODUCT IMAGE
# =====================================================

@app.route(
    "/api/admin/products/upload-image",
    methods=["POST"],
)
@admin_required
def upload_product_image():
    try:
        if "image" not in request.files:
            return json_error("No image received.", 400)

        image = request.files["image"]

        if not image.filename:
            return json_error("No image selected.", 400)

        if not allowed_file(image.filename):
            return json_error(
                "Only JPG, JPEG, PNG and WEBP images are allowed.",
                400,
            )

        if image.mimetype not in ALLOWED_IMAGE_MIMETYPES:
            return json_error("Invalid image file type.", 400)

        original_name = secure_filename(image.filename)

        if not original_name or "." not in original_name:
            return json_error("Invalid image filename.", 400)

        extension = original_name.rsplit(".", 1)[1].lower()
        unique_name = f"product_{secrets.token_hex(12)}.{extension}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_name)

        image.save(save_path)

        return jsonify({
            "success": True,
            "message": "Product image uploaded successfully.",
            "filename": unique_name,
        }), 201

    except Exception as error:
        print("Product image upload error:", error)
        return json_error("Unable to upload product image.", 500)


# =====================================================
# CUSTOMER - CREATE PRODUCT ORDER
# =====================================================

@app.route(
    "/api/orders",
    methods=["POST"],
)
def create_order():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return json_error("No order information received.", 400)

        try:
            product_id = int(data.get("productId"))
        except (TypeError, ValueError):
            return json_error("Invalid product.", 400)

        customer_name = str(data.get("customerName", "")).strip()
        phone = str(data.get("phone", "")).strip()

        try:
            quantity = int(data.get("quantity", 1))
        except (TypeError, ValueError):
            return json_error("Invalid quantity.", 400)

        if not customer_name:
            return json_error("Please enter your name.", 400)

        if not phone:
            return json_error("Please enter your phone number.", 400)

        if quantity < 1:
            return json_error("Quantity must be at least 1.", 400)

        if quantity > 100:
            return json_error("Quantity is too large.", 400)

        product = get_product(product_id)

        if not product:
            return json_error("Product not found.", 404)

        if product["stock_status"] == "Out of Stock":
            return json_error(
                "This product is currently out of stock.",
                400,
            )

        unit_price = int(product["price"])
        total_price = unit_price * quantity
        order_id = generate_order_id()

        add_order(
            order_id,
            product["id"],
            product["name"],
            customer_name,
            phone,
            quantity,
            unit_price,
            total_price,
        )

        return jsonify({
            "success": True,
            "message": "Order placed successfully.",
            "orderId": order_id,
            "productName": product["name"],
            "quantity": quantity,
            "unitPrice": unit_price,
            "totalPrice": total_price,
            "status": "Pending",
        }), 201

    except Exception as error:
        print("Create order error:", error)
        return json_error("Unable to place order.", 500)


# =====================================================
# CUSTOMER - TRACK ORDER
# =====================================================

@app.route(
    "/api/orders/<order_id>",
    methods=["GET"],
)
def track_order(order_id):
    try:
        order_id = order_id.strip().upper()
        order = get_order(order_id)

        if not order:
            return json_error("Order not found.", 404)

        # Do not expose full customer PII on a public tracking endpoint.
        return jsonify({
            "success": True,
            "order": {
                "orderId": order["order_id"],
                "productName": order["product_name"],
                "customerName": masked_name(order["customer_name"]),
                "phone": masked_phone(order["phone"]),
                "quantity": order["quantity"],
                "unitPrice": order["unit_price"],
                "totalPrice": order["total_price"],
                "status": order["status"],
                "createdAt": order["created_at"],
            },
        }), 200

    except Exception as error:
        print("Track order error:", error)
        return json_error("Unable to track order.", 500)


# =====================================================
# ADMIN - GET ALL ORDERS
# =====================================================

@app.route(
    "/api/admin/orders",
    methods=["GET"],
)
@admin_required
def admin_orders():
    try:
        orders = get_all_orders()

        results = [
            {
                "orderId": order["order_id"],
                "productId": order["product_id"],
                "productName": order["product_name"],
                "customerName": order["customer_name"],
                "phone": order["phone"],
                "quantity": order["quantity"],
                "unitPrice": order["unit_price"],
                "totalPrice": order["total_price"],
                "status": order["status"],
                "createdAt": order["created_at"],
            }
            for order in orders
        ]

        return jsonify({
            "success": True,
            "orders": results,
        }), 200

    except Exception as error:
        print("Admin orders error:", error)
        return json_error("Unable to load orders.", 500)


# =====================================================
# ADMIN - UPDATE ORDER STATUS
# =====================================================

@app.route(
    "/api/admin/orders/<order_id>/status",
    methods=["PUT"],
)
@admin_required
def change_order_status(order_id):
    try:
        order_id = order_id.strip().upper()
        order = get_order(order_id)

        if not order:
            return json_error("Order not found.", 404)

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return json_error("No status received.", 400)

        new_status = str(data.get("status", "")).strip()

        allowed_statuses = {
            "Pending",
            "Confirmed",
            "Ready",
            "Completed",
            "Cancelled",
        }

        if new_status not in allowed_statuses:
            return json_error("Invalid order status.", 400)

        update_order_status(
            order_id,
            new_status,
        )

        return jsonify({
            "success": True,
            "message": "Order status updated successfully.",
            "orderId": order_id,
            "status": new_status,
        }), 200

    except Exception as error:
        print("Order status update error:", error)
        return json_error("Unable to update order status.", 500)


# =====================================================
# ADMIN - DELETE ORDER
# =====================================================

@app.route(
    "/api/admin/orders/<order_id>",
    methods=["DELETE"],
)
@admin_required
def admin_delete_order(order_id):
    try:
        order_id = order_id.strip().upper()
        order = get_order(order_id)

        if not order:
            return json_error("Order not found.", 404)

        delete_order(order_id)

        return jsonify({
            "success": True,
            "message": "Order deleted successfully.",
        }), 200

    except Exception as error:
        print("Delete order error:", error)
        return json_error("Unable to delete order.", 500)


# =====================================================
# 413 - FILE TOO LARGE
# =====================================================

@app.errorhandler(413)
def file_too_large(error):
    return json_error(
        "Image is too large. Maximum size is 5MB.",
        413,
    )


# =====================================================
# 404 ERROR
# =====================================================

@app.errorhandler(404)
def page_not_found(error):
    if request.path.startswith("/api/"):
        return json_error("API endpoint not found.", 404)

    return (
        "<h1>404</h1>"
        "<p>Page not found.</p>"
        '<p><a href="/">Return to CoreFix</a></p>',
        404,
    )


# =====================================================
# RUN APPLICATION LOCALLY
# =====================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )
