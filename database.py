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
    contact_method
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            INSERT INTO repairs (

                repair_id,
                name,
                phone,
                device,
                brand,
                model,
                issue,
                description,
                contact_method

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repair_id,
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
    total_price
):

    connection = get_connection()

    try:

        execute_query(
            connection,
            """
            INSERT INTO orders (

                order_id,
                product_id,
                product_name,
                customer_name,
                phone,
                quantity,
                unit_price,
                total_price

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
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