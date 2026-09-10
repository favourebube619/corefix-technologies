import os
import sqlite3

from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

SQLITE_DATABASE = BASE_DIR / "corefix.db"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
).strip()

USE_POSTGRES = bool(DATABASE_URL)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():

    if USE_POSTGRES:

        connection = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )

        return connection

    connection = sqlite3.connect(
        SQLITE_DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# EXECUTE HELPER
# ==========================================

def execute_query(
    connection,
    query,
    parameters=()
):

    if USE_POSTGRES:

        query = query.replace(
            "?",
            "%s"
        )

        cursor = connection.cursor()

        cursor.execute(
            query,
            parameters
        )

        return cursor

    return connection.execute(
        query,
        parameters
    )


# ==========================================
# CREATE DATABASE TABLES
# ==========================================

def create_database():

    connection = get_connection()

    try:

        # ==================================
        # REPAIRS TABLE
        # ==================================

        if USE_POSTGRES:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS repairs (

                    id SERIAL PRIMARY KEY,

                    repair_id TEXT UNIQUE NOT NULL,

                    user_id INTEGER,

                    name TEXT NOT NULL,

                    phone TEXT NOT NULL,

                    device TEXT NOT NULL,

                    brand TEXT NOT NULL,

                    model TEXT NOT NULL,

                    issue TEXT NOT NULL,

                    description TEXT NOT NULL,

                    contact_method TEXT NOT NULL,

                    status TEXT NOT NULL
                        DEFAULT 'Request Received',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

        else:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS repairs (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    repair_id TEXT UNIQUE NOT NULL,

                    user_id INTEGER,

                    name TEXT NOT NULL,

                    phone TEXT NOT NULL,

                    device TEXT NOT NULL,

                    brand TEXT NOT NULL,

                    model TEXT NOT NULL,

                    issue TEXT NOT NULL,

                    description TEXT NOT NULL,

                    contact_method TEXT NOT NULL,

                    status TEXT NOT NULL
                        DEFAULT 'Request Received',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )




        # ==================================
        # PRODUCTS TABLE
        # ==================================

        if USE_POSTGRES:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS products (

                    id SERIAL PRIMARY KEY,

                    name TEXT NOT NULL,

                    description TEXT NOT NULL,

                    price INTEGER NOT NULL,

                    icon TEXT NOT NULL
                        DEFAULT '📦',

                    stock_status TEXT NOT NULL
                        DEFAULT 'In Stock',

                    image TEXT
                        DEFAULT '',

                    image_public_id TEXT
                        DEFAULT '',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

        else:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS products (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT NOT NULL,

                    description TEXT NOT NULL,

                    price INTEGER NOT NULL,

                    icon TEXT NOT NULL
                        DEFAULT '📦',

                    stock_status TEXT NOT NULL
                        DEFAULT 'In Stock',

                    image TEXT
                        DEFAULT '',

                    image_public_id TEXT
                        DEFAULT '',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )


        # ==================================
        # PRODUCT TABLE MIGRATION
        # ==================================
        #
        # Existing databases were created
        # before image_public_id existed.
        #
        # CREATE TABLE IF NOT EXISTS does
        # not add new columns to an existing
        # table, so we migrate it safely.
        # ==================================

        if USE_POSTGRES:

            execute_query(
                connection,
                """
                ALTER TABLE products
                ADD COLUMN IF NOT EXISTS
                image_public_id TEXT
                DEFAULT ''
                """
            )

        else:

            cursor = execute_query(
                connection,
                """
                PRAGMA table_info(products)
                """
            )

            columns = [
                row["name"]
                for row in cursor.fetchall()
            ]

            if "image_public_id" not in columns:

                execute_query(
                    connection,
                    """
                    ALTER TABLE products
                    ADD COLUMN image_public_id TEXT
                    DEFAULT ''
                    """
                )


        # ==================================
        # ORDERS TABLE
        # ==================================

        if USE_POSTGRES:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS orders (

                    id SERIAL PRIMARY KEY,

                    order_id TEXT UNIQUE NOT NULL,

                    user_id INTEGER,

                    product_id INTEGER NOT NULL,

                    product_name TEXT NOT NULL,

                    customer_name TEXT NOT NULL,

                    phone TEXT NOT NULL,

                    quantity INTEGER NOT NULL
                        DEFAULT 1,

                    unit_price INTEGER NOT NULL,

                    total_price INTEGER NOT NULL,

                    status TEXT NOT NULL
                        DEFAULT 'Pending',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

        else:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS orders (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    order_id TEXT UNIQUE NOT NULL,

                    user_id INTEGER,

                    product_id INTEGER NOT NULL,

                    product_name TEXT NOT NULL,

                    customer_name TEXT NOT NULL,

                    phone TEXT NOT NULL,

                    quantity INTEGER NOT NULL
                        DEFAULT 1,

                    unit_price INTEGER NOT NULL,

                    total_price INTEGER NOT NULL,

                    status TEXT NOT NULL
                        DEFAULT 'Pending',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )


        # ==================================
        # USERS TABLE
        # ==================================

        if USE_POSTGRES:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS users (

                    id SERIAL PRIMARY KEY,

                    name TEXT NOT NULL,

                    email TEXT UNIQUE NOT NULL,

                    phone TEXT NOT NULL,

                    password_hash TEXT NOT NULL,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

        else:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS users (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT NOT NULL,

                    email TEXT UNIQUE NOT NULL,

                    phone TEXT NOT NULL,

                    password_hash TEXT NOT NULL,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )


        # ==================================
        # ACCOUNT LINK MIGRATIONS
        # ==================================

        if USE_POSTGRES:

            execute_query(
                connection,
                """
                ALTER TABLE repairs
                ADD COLUMN IF NOT EXISTS user_id INTEGER
                """
            )

            execute_query(
                connection,
                """
                ALTER TABLE orders
                ADD COLUMN IF NOT EXISTS user_id INTEGER
                """
            )

        else:

            repair_columns = [
                row["name"]
                for row in execute_query(
                    connection,
                    "PRAGMA table_info(repairs)"
                ).fetchall()
            ]

            if "user_id" not in repair_columns:
                execute_query(
                    connection,
                    """
                    ALTER TABLE repairs
                    ADD COLUMN user_id INTEGER
                    """
                )

            order_columns = [
                row["name"]
                for row in execute_query(
                    connection,
                    "PRAGMA table_info(orders)"
                ).fetchall()
            ]

            if "user_id" not in order_columns:
                execute_query(
                    connection,
                    """
                    ALTER TABLE orders
                    ADD COLUMN user_id INTEGER
                    """
                )



        # ==================================
        # PUSH SUBSCRIPTIONS TABLE
        # ==================================

        if USE_POSTGRES:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS push_subscriptions (

                    id SERIAL PRIMARY KEY,

                    user_id INTEGER NOT NULL,

                    endpoint TEXT UNIQUE NOT NULL,

                    p256dh TEXT NOT NULL,

                    auth TEXT NOT NULL,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

        else:

            execute_query(
                connection,
                """
                CREATE TABLE IF NOT EXISTS push_subscriptions (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_id INTEGER NOT NULL,

                    endpoint TEXT UNIQUE NOT NULL,

                    p256dh TEXT NOT NULL,

                    auth TEXT NOT NULL,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

        # ==================================
        # INDEXES
        # ==================================

        execute_query(
            connection,
            """
            CREATE INDEX IF NOT EXISTS
            idx_repairs_repair_id
            ON repairs(repair_id)
            """
        )

        execute_query(
            connection,
            """
            CREATE INDEX IF NOT EXISTS
            idx_repairs_status
            ON repairs(status)
            """
        )

        execute_query(
            connection,
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_order_id
            ON orders(order_id)
            """
        )

        execute_query(
            connection,
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_status
            ON orders(status)
            """
        )

        execute_query(
            connection,
            """
            CREATE INDEX IF NOT EXISTS
            idx_repairs_user_id
            ON repairs(user_id)
            """
        )

        execute_query(
            connection,
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_user_id
            ON orders(user_id)
            """
        )

        # Save all database changes
        connection.commit()

    finally:
        connection.close()

# =====================================================
# PUSH NOTIFICATION SUBSCRIPTIONS
# =====================================================

def save_push_subscription(user_id, endpoint, p256dh, auth):

    connection = get_connection()

    try:

        if USE_POSTGRES:

            execute_query(
                connection,
                """
                INSERT INTO push_subscriptions (
                    user_id,
                    endpoint,
                    p256dh,
                    auth
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT (endpoint)
                DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    p256dh = EXCLUDED.p256dh,
                    auth = EXCLUDED.auth
                """,
                (
                    user_id,
                    endpoint,
                    p256dh,
                    auth,
                ),
            )

        else:

            execute_query(
                connection,
                """
                INSERT INTO push_subscriptions (
                    user_id,
                    endpoint,
                    p256dh,
                    auth
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(endpoint)
                DO UPDATE SET
                    user_id = excluded.user_id,
                    p256dh = excluded.p256dh,
                    auth = excluded.auth
                """,
                (
                    user_id,
                    endpoint,
                    p256dh,
                    auth,
                ),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_push_subscriptions_by_user_id(user_id):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT
                id,
                user_id,
                endpoint,
                p256dh,
                auth,
                created_at
            FROM push_subscriptions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )

        return cursor.fetchall()

    finally:
        connection.close()


def delete_push_subscription(endpoint):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            DELETE FROM push_subscriptions
            WHERE endpoint = ?
            """,
            (endpoint,),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

# ==========================================
# ADD USER
# ==========================================

def add_user(
    name,
    email,
    phone,
    password_hash
):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            INSERT INTO users (

                name,
                email,
                phone,
                password_hash

            )

            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                phone,
                password_hash
            )
        )

        connection.commit()

        return cursor.lastrowid if not USE_POSTGRES else None

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# GET USER BY EMAIL
# ==========================================

def get_user_by_email(
    email
):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM users
            WHERE LOWER(email) = LOWER(?)
            """,
            (
                email,
            )
        )

        return cursor.fetchone()

    finally:

        connection.close()


# ==========================================
# GET USER BY ID
# ==========================================

def get_user_by_id(
    user_id
):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            )
        )

        return cursor.fetchone()

    finally:

        connection.close()


        # ==========================================
# UPDATE USER PROFILE
# ==========================================

def update_user(
    user_id,
    name,
    email,
    phone
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            UPDATE users

            SET
                name = ?,
                email = ?,
                phone = ?

            WHERE id = ?
            """,
            (
                name,
                email,
                phone,
                user_id
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


        # ==========================================
# UPDATE USER PASSWORD
# ==========================================

def update_user_password(
    user_id,
    password_hash
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                password_hash,
                user_id
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# ADD REPAIR
# ==========================================

def add_repair(
    repair_id,
    name,
    phone,
    device,
    brand,
    model,
    issue,
    description,
    contact_method,
    user_id=None
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            INSERT INTO repairs (

                repair_id,
                user_id,
                name,
                phone,
                device,
                brand,
                model,
                issue,
                description,
                contact_method

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repair_id,
                user_id,
                name,
                phone,
                device,
                brand,
                model,
                issue,
                description,
                contact_method
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# GET ONE REPAIR
# ==========================================

def get_repair(
    repair_id
):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM repairs
            WHERE repair_id = ?
            """,
            (
                repair_id,
            )
        )

        return cursor.fetchone()

    finally:

        connection.close()


# ==========================================
# GET ALL REPAIRS
# ==========================================

def get_all_repairs():

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM repairs
            ORDER BY id DESC
            """
        )

        return cursor.fetchall()

    finally:

        connection.close()


# ==========================================
# GET REPAIRS BY USER
# ==========================================

def get_repairs_by_user_id(
    user_id
):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM repairs
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (
                user_id,
            )
        )

        return cursor.fetchall()

    finally:

        connection.close()


# ==========================================
# UPDATE REPAIR STATUS
# ==========================================

def update_repair_status(
    repair_id,
    status
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            UPDATE repairs

            SET status = ?

            WHERE repair_id = ?
            """,
            (
                status,
                repair_id
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# ADD PRODUCT
# ==========================================

def add_product(
    name,
    description,
    price,
    icon,
    stock_status,
    image,
    image_public_id=""
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            INSERT INTO products (

                name,
                description,
                price,
                icon,
                stock_status,
                image,
                image_public_id

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                price,
                icon,
                stock_status,
                image,
                image_public_id
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# GET ALL PRODUCTS
# ==========================================

def get_all_products():

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM products
            ORDER BY id DESC
            """
        )

        return cursor.fetchall()

    finally:

        connection.close()


# ==========================================
# GET ONE PRODUCT
# ==========================================

def get_product(
    product_id
):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM products
            WHERE id = ?
            """,
            (
                product_id,
            )
        )

        return cursor.fetchone()

    finally:

        connection.close()


# ==========================================
# UPDATE PRODUCT
# ==========================================

def update_product(
    product_id,
    name,
    description,
    price,
    icon,
    stock_status,
    image,
    image_public_id=""
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            UPDATE products

            SET
                name = ?,
                description = ?,
                price = ?,
                icon = ?,
                stock_status = ?,
                image = ?,
                image_public_id = ?

            WHERE id = ?
            """,
            (
                name,
                description,
                price,
                icon,
                stock_status,
                image,
                image_public_id,
                product_id
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# DELETE PRODUCT
# ==========================================

def delete_product(
    product_id
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            DELETE FROM products
            WHERE id = ?
            """,
            (
                product_id,
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# ADD ORDER
# ==========================================

def add_order(
    order_id,
    product_id,
    product_name,
    customer_name,
    phone,
    quantity,
    unit_price,
    total_price,
    user_id=None
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            INSERT INTO orders (

                order_id,
                user_id,
                product_id,
                product_name,
                customer_name,
                phone,
                quantity,
                unit_price,
                total_price

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                user_id,
                product_id,
                product_name,
                customer_name,
                phone,
                quantity,
                unit_price,
                total_price
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# GET ONE ORDER
# ==========================================

def get_order(
    order_id
):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM orders
            WHERE order_id = ?
            """,
            (
                order_id,
            )
        )

        return cursor.fetchone()

    finally:

        connection.close()


# ==========================================
# GET ALL ORDERS
# ==========================================

def get_all_orders():

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM orders
            ORDER BY id DESC
            """
        )

        return cursor.fetchall()

    finally:

        connection.close()


# ==========================================
# GET ORDERS BY USER
# ==========================================

def get_orders_by_user_id(
    user_id
):

    connection = get_connection()

    try:

        cursor = execute_query(
            connection,
            """
            SELECT *
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (
                user_id,
            )
        )

        return cursor.fetchall()

    finally:

        connection.close()


# ==========================================
# UPDATE ORDER STATUS
# ==========================================

def update_order_status(
    order_id,
    status
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            UPDATE orders

            SET status = ?

            WHERE order_id = ?
            """,
            (
                status,
                order_id
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ==========================================
# DELETE ORDER
# ==========================================

def delete_order(
    order_id
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            DELETE FROM orders
            WHERE order_id = ?
            """,
            (
                order_id,
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()
