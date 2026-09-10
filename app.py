# =====================================================
# COREFIX TECHNOLOGIES
# FLASK BACKEND
# REPAIRS + PRODUCTS + IMAGES + ORDERS
# =====================================================

import cloudinary
import cloudinary.uploader
import hmac
import os
import secrets
import smtplib
import json
from email.message import EmailMessage
from datetime import datetime, timedelta
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import send_from_directory
from pywebpush import webpush, WebPushException

from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from database import (
    # Repairs
    create_database,
    add_repair,
    get_repair,
    get_all_repairs,
    get_repairs_by_user_id,
    update_repair_status,
    save_push_subscription,
    get_push_subscriptions_by_user_id,
    delete_push_subscription,

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
    get_orders_by_user_id,
    update_order_status,
    delete_order,

    # Users
    add_user,
    get_user_by_email,
    get_user_by_id,
    update_user_password,
)


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "").strip()
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "").strip()

CLOUDINARY_CONFIGURED = all(
    [
        CLOUDINARY_CLOUD_NAME,
        CLOUDINARY_API_KEY,
        CLOUDINARY_API_SECRET,
    ]
)

if CLOUDINARY_CONFIGURED:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )


    # =====================================================
# WEB PUSH / VAPID CONFIGURATION
# =====================================================

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL")


# =====================================================
# FLASK APPLICATION
# =====================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "corefix-local-development-secret-key"
)


# =====================================================
# PASSWORD RESET CONFIGURATION
# =====================================================

password_reset_serializer = URLSafeTimedSerializer(
    app.secret_key
)

PASSWORD_RESET_MAX_AGE = 1800  # 30 minutes


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


def customer_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def allowed_file(filename):
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def delete_cloudinary_image(public_id):
    """Safely delete a Cloudinary image by public_id."""
    public_id = str(public_id or "").strip()

    if not public_id:
        return True

    if not CLOUDINARY_CONFIGURED:
        print("Cloudinary cleanup skipped: Cloudinary is not configured.")
        return False

    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type="image",
            invalidate=True,
        )
        status = str(result.get("result", "")).lower()

        if status in {"ok", "not found"}:
            return True

        print("Cloudinary cleanup warning:", public_id, result)
        return False

    except Exception as error:
        print("Cloudinary cleanup error:", public_id, error)
        return False


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


def send_reset_email(recipient_email, reset_url):

    mail_server = os.getenv("MAIL_SERVER", "").strip()
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_username = os.getenv("MAIL_USERNAME", "").strip()
    mail_password = os.getenv("MAIL_PASSWORD", "").strip()
    mail_from = os.getenv("MAIL_FROM", mail_username).strip()

    if not all([
        mail_server,
        mail_username,
        mail_password,
        mail_from
    ]):
        raise RuntimeError(
            "Email settings are not fully configured."
        )

    message = EmailMessage()

    message["Subject"] = "Reset your CoreFix password"
    message["From"] = mail_from
    message["To"] = recipient_email

    message.set_content(
        f"""
Hello,

A password reset was requested for your CoreFix account.

Use the link below to create a new password:

{reset_url}

This link expires in 30 minutes.

If you did not request this password reset, you can ignore this email.

CoreFix Technologies
"""
    )

    with smtplib.SMTP(
        mail_server,
        mail_port
    ) as server:

        server.starttls()

        server.login(
            mail_username,
            mail_password
        )

        server.send_message(message)


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():
    user = None

    if session.get("user_id"):
        user = get_user_by_id(session["user_id"])

        if not user:
            session.clear()

    return render_template(
        "index.html",
        user=user,
    )


# =====================================================
# CUSTOMER AUTHENTICATION - SIGN UP
# =====================================================

@app.route(
    "/signup",
    methods=["GET", "POST"],
)
def signup():
    if session.get("user_id"):
        return redirect(url_for("customer_dashboard"))

    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name:
            error = "Please enter your full name."
        elif not email or "@" not in email:
            error = "Please enter a valid email address."
        elif not phone:
            error = "Please enter your phone number."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif get_user_by_email(email):
            error = "An account with this email already exists."
        else:
            try:
                password_hash = generate_password_hash(password)

                add_user(
                    name,
                    email,
                    phone,
                    password_hash,
                )

                user = get_user_by_email(email)

                if not user:
                    error = "Account was created, but login could not be completed."
                else:
                    session.clear()
                    session["user_id"] = user["id"]
                    session["user_name"] = user["name"]
                    session.permanent = True

                    return redirect(url_for("customer_dashboard"))

            except Exception as signup_error:
                print("Signup error:", signup_error)
                error = "Unable to create your account right now."

    return render_template(
        "signup.html",
        error=error,
    )


# =====================================================
# CUSTOMER AUTHENTICATION - LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"],
)
def login():
    if session.get("user_id"):
        return redirect(url_for("customer_dashboard"))

    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email) if email else None

        if not user or not check_password_hash(user["password_hash"], password):
            error = "Invalid email or password."
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session.permanent = True

            return redirect(url_for("customer_dashboard"))

    return render_template(
        "login.html",
        error=error,
    )


# =====================================================
# OFFLINE PAGE
# =====================================================

@app.route("/offline")
def offline():
    return render_template("offline.html")


@app.route("/service-worker.js")
def service_worker():
    response = send_from_directory(
        "static/pwa",
        "service-worker.js"
    )

    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"

    return response


@app.route("/push/subscribe", methods=["POST"])
@customer_required
def push_subscribe():
    data = request.get_json(silent=True) or {}

    endpoint = data.get("endpoint")
    keys = data.get("keys") or {}

    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not endpoint or not p256dh or not auth:
        return jsonify({
            "success": False,
            "message": "Invalid push subscription."
        }), 400

    save_push_subscription(
        session["user_id"],
        endpoint,
        p256dh,
        auth,
    )

    return jsonify({
        "success": True,
        "message": "Push notifications enabled."
    })

@app.route("/push/test", methods=["POST"])
@customer_required
def push_test():

    subscriptions = get_push_subscriptions_by_user_id(
        session["user_id"]
    )

    if not subscriptions:
        return jsonify({
            "success": False,
            "message": "No push subscription found."
        }), 404

    payload = {
        "title": "CoreFix Technologies",
        "body": "Push notifications are working successfully.",
        "icon": "/static/assets/corefix-icon-192.png",
        "badge": "/static/assets/corefix-icon-192.png",
        "url": "/dashboard"
    }

    sent = 0

    for subscription in subscriptions:

        try:
            webpush(
                subscription_info={
                    "endpoint": subscription["endpoint"],
                    "keys": {
                        "p256dh": subscription["p256dh"],
                        "auth": subscription["auth"],
                    },
                },
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": VAPID_CLAIMS_EMAIL
                },
            )

            sent += 1

        except WebPushException as error:
            print("Push notification error:", error)

    return jsonify({
        "success": True,
        "sent": sent
    })


# =====================================================
# CUSTOMER DASHBOARD
# =====================================================

@app.route("/dashboard")
@customer_required
def customer_dashboard():

    user = get_user_by_id(
        session["user_id"]
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))

    repairs = get_repairs_by_user_id(
        user["id"]
    )

    orders = get_orders_by_user_id(
        user["id"]
    )

    notifications = []


    for repair in repairs:

        if repair["status"] == "Ready for Collection":

            notifications.append({
                "type": "repair",
                "icon": "fa-screwdriver-wrench",
                "title": "Repair Ready",
                "message": (
                    f'{repair["brand"]} '
                    f'{repair["model"]} '
                    "is ready for collection."
                ),
                "reference": repair["repair_id"],
            })


    for order in orders:

        if order["status"] == "Ready":

            notifications.append({
                "type": "order",
                "icon": "fa-box",
                "title": "Order Ready",
                "message": (
                    f'{order["product_name"]} '
                    "is ready."
                ),
                "reference": order["order_id"],
            })

        elif order["status"] == "Completed":

            notifications.append({
                "type": "completed",
                "icon": "fa-circle-check",
                "title": "Order Completed",
                "message": (
                    f'Your order for '
                    f'{order["product_name"]} '
                    "has been completed."
                ),
                "reference": order["order_id"],
            })


    return render_template(
    "dashboard.html",
    user=user,
    repairs=repairs,
    orders=orders,
    notifications=notifications,
    VAPID_PUBLIC_KEY=VAPID_PUBLIC_KEY,
)


    # =================================================
# CUSTOMER NOTIFICATIONS
# =================================================

notifications = []





# =====================================================
# EDIT CUSTOMER PROFILE
# =====================================================

@app.route(
    "/profile/edit",
    methods=["GET", "POST"],
)
@customer_required
def edit_profile():

    user = get_user_by_id(
        session["user_id"]
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))

    error = None
    success = None

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        if not name:

            error = "Please enter your full name."

        elif not email or "@" not in email:

            error = "Please enter a valid email address."

        elif not phone:

            error = "Please enter your phone number."

        else:

            existing_user = get_user_by_email(
                email
            )

            if (
                existing_user
                and existing_user["id"] != user["id"]
            ):

                error = (
                    "Another account is already "
                    "using this email address."
                )

            else:

                try:

                    update_user(
                        user["id"],
                        name,
                        email,
                        phone,
                    )

                    session["user_name"] = name

                    user = get_user_by_id(
                        session["user_id"]
                    )

                    success = (
                        "Your profile has been "
                        "updated successfully."
                    )

                except Exception as profile_error:

                    print(
                        "Profile update error:",
                        profile_error
                    )

                    error = (
                        "Unable to update your "
                        "profile right now."
                    )

    return render_template(
        "edit_profile.html",
        user=user,
        error=error,
        success=success,
    )


# =====================================================
# CHANGE CUSTOMER PASSWORD
# =====================================================

@app.route(
    "/profile/change-password",
    methods=["GET", "POST"],
)
@customer_required
def change_password():

    user = get_user_by_id(
        session["user_id"]
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))

    error = None
    success = None

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not check_password_hash(
            user["password_hash"],
            current_password
        ):

            error = "Your current password is incorrect."

        elif len(new_password) < 8:

            error = (
                "Your new password must be "
                "at least 8 characters."
            )

        elif new_password != confirm_password:

            error = "The new passwords do not match."

        elif check_password_hash(
            user["password_hash"],
            new_password
        ):

            error = (
                "Your new password must be "
                "different from your current password."
            )

        else:

            try:

                new_password_hash = generate_password_hash(
                    new_password
                )

                update_user_password(
                    user["id"],
                    new_password_hash
                )

                success = (
                    "Your password has been "
                    "changed successfully."
                )

            except Exception as password_error:

                print(
                    "Password update error:",
                    password_error
                )

                error = (
                    "Unable to change your "
                    "password right now."
                )

    return render_template(
        "change_password.html",
        user=user,
        error=error,
        success=success,
    )


# =====================================================
# FORGOT PASSWORD
# =====================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"],
)
def forgot_password():

    message = None

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        user = get_user_by_email(email)

        # Always show the same response.
        # This prevents people from checking
        # which email addresses are registered.
        message = (
            "If an account exists with that email, "
            "a password reset link has been created."
        )

        if user:

            token = password_reset_serializer.dumps(
                user["email"],
                salt="password-reset"
            )

            reset_url = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            try:

                send_reset_email(
                    user["email"],
                    reset_url
                )

            except Exception as email_error:

                print(
                    "Password reset email error:",
                    email_error
                )

                # Local development fallback
                print("\n" + "=" * 60)
                print("COREFIX PASSWORD RESET LINK")
                print(reset_url)
                print("=" * 60 + "\n")


    return render_template(
        "forgot_password.html",
        message=message,
    )


# =====================================================
# RESET PASSWORD
# =====================================================

@app.route(
    "/reset-password/<token>",
    methods=["GET", "POST"],
)
def reset_password(token):

    try:

        email = password_reset_serializer.loads(
            token,
            salt="password-reset",
            max_age=PASSWORD_RESET_MAX_AGE
        )

    except SignatureExpired:

        return render_template(
            "reset_password.html",
            invalid_token=True,
            error=(
                "This password reset link has expired. "
                "Please request a new one."
            ),
        )

    except BadSignature:

        return render_template(
            "reset_password.html",
            invalid_token=True,
            error=(
                "This password reset link is invalid."
            ),
        )

    user = get_user_by_email(email)

    if not user:

        return render_template(
            "reset_password.html",
            invalid_token=True,
            error="This password reset link is invalid.",
        )

    error = None

    if request.method == "POST":

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if len(new_password) < 8:

            error = (
                "Your password must be "
                "at least 8 characters."
            )

        elif new_password != confirm_password:

            error = "The passwords do not match."

        else:

            new_password_hash = generate_password_hash(
                new_password
            )

            update_user_password(
                user["id"],
                new_password_hash
            )

            return redirect(
                url_for(
                    "login",
                    reset="success"
                )
            )

    return render_template(
        "reset_password.html",
        invalid_token=False,
        error=error,
    )


# =====================================================
# CUSTOMER LOGOUT
# =====================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


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

        user_id = session.get("user_id")

        if user_id:
            account_user = get_user_by_id(user_id)

            if account_user:
                name = account_user["name"]
                phone = account_user["phone"]

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
            user_id,
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
                "imagePublicId": product["image_public_id"] or "",
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
        image_public_id = str(data.get("imagePublicId", "")).strip()

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
            image_public_id,
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
        old_image = str(product["image"] or "").strip()
        old_image_public_id = str(product["image_public_id"] or "").strip()

        image = str(
            data.get("image", old_image)
        ).strip()

        if "imagePublicId" in data:
            image_public_id = str(data.get("imagePublicId", "")).strip()
        elif image == old_image:
            image_public_id = old_image_public_id
        else:
            image_public_id = ""

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
            image_public_id,
        )

        if old_image_public_id and old_image_public_id != image_public_id:
            delete_cloudinary_image(old_image_public_id)

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

        image_public_id = str(product["image_public_id"] or "").strip()

        delete_product(product_id)

        if image_public_id:
            delete_cloudinary_image(image_public_id)

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
        if not CLOUDINARY_CONFIGURED:
            return json_error(
                "Cloudinary is not configured on the server.",
                500,
            )

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

        upload_result = cloudinary.uploader.upload(
            image,
            folder="corefix/products",
            resource_type="image",
            use_filename=False,
            unique_filename=True,
            overwrite=False,
        )

        image_url = str(
            upload_result.get("secure_url", "")
        ).strip()

        image_public_id = str(
            upload_result.get("public_id", "")
        ).strip()

        if not image_url or not image_public_id:
            if image_public_id:
                delete_cloudinary_image(image_public_id)

            return json_error(
                "Cloud image upload failed.",
                500,
            )

        return jsonify({
            "success": True,
            "message": "Product image uploaded successfully.",
            "filename": image_url,
            "publicId": image_public_id,
        }), 201

    except Exception as error:
        print("Product image upload error:", error)
        return json_error(
            "Unable to upload product image.",
            500,
        )


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

        user_id = session.get("user_id")

        if user_id:
            account_user = get_user_by_id(user_id)

            if account_user:
                customer_name = account_user["name"]
                phone = account_user["phone"]

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
            user_id,
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
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False,
        use_reloader=False,
    )