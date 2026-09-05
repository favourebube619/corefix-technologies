import sqlite3
from pathlib import Path


# ==========================================
# DATABASE LOCATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "corefix.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# CREATE DATABASE
# ==========================================

def create_database():

    connection = get_connection()

    try:

        # ==================================
        # REPAIRS TABLE
        # ==================================

        connection.execute("""
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
        """)


        # ==================================
        # PRODUCTS TABLE
        # ==================================

        connection.execute("""
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

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP

            )
        """)


        # ==================================
        # ORDERS TABLE
        # ==================================

        connection.execute("""
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
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)

            )
        """)


        # ==================================
        # MIGRATION:
        # ADD IMAGE COLUMN IF MISSING
        # ==================================

        product_columns = connection.execute(
            """
            PRAGMA table_info(products)
            """
        ).fetchall()


        column_names = {
            column["name"]
            for column in product_columns
        }


        if "image" not in column_names:

            connection.execute("""
                ALTER TABLE products
                ADD COLUMN image TEXT
                DEFAULT ''
            """)


        # ==================================
        # INDEXES
        # ==================================

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_repairs_repair_id
            ON repairs(repair_id)
        """)


        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_repairs_status
            ON repairs(status)
        """)


        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_orders_order_id
            ON orders(order_id)
        """)


        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_orders_status
            ON orders(status)
        """)


        connection.commit()


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

        connection.execute("""
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

        """, (

            repair_id,
            name,
            phone,
            device,
            brand,
            model,
            issue,
            description,
            contact_method

        ))

        connection.commit()


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

        repair = connection.execute("""
            SELECT *
            FROM repairs
            WHERE repair_id = ?
        """, (
            repair_id,
        )).fetchone()

        return repair


    finally:

        connection.close()


# ==========================================
# GET ALL REPAIRS
# ==========================================

def get_all_repairs():

    connection = get_connection()

    try:

        repairs = connection.execute("""
            SELECT *
            FROM repairs
            ORDER BY id DESC
        """).fetchall()

        return repairs


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

        connection.execute("""
            UPDATE repairs
            SET status = ?
            WHERE repair_id = ?
        """, (
            status,
            repair_id
        ))

        connection.commit()


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
    image
):

    connection = get_connection()

    try:

        connection.execute("""
            INSERT INTO products (

                name,
                description,
                price,
                icon,
                stock_status,
                image

            )

            VALUES (?, ?, ?, ?, ?, ?)

        """, (

            name,
            description,
            price,
            icon,
            stock_status,
            image

        ))

        connection.commit()


    finally:

        connection.close()


# ==========================================
# GET ALL PRODUCTS
# ==========================================

def get_all_products():

    connection = get_connection()

    try:

        products = connection.execute("""
            SELECT *
            FROM products
            ORDER BY id DESC
        """).fetchall()

        return products


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

        product = connection.execute("""
            SELECT *
            FROM products
            WHERE id = ?
        """, (
            product_id,
        )).fetchone()

        return product


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
    image
):

    connection = get_connection()

    try:

        connection.execute("""
            UPDATE products

            SET
                name = ?,
                description = ?,
                price = ?,
                icon = ?,
                stock_status = ?,
                image = ?

            WHERE id = ?
        """, (

            name,
            description,
            price,
            icon,
            stock_status,
            image,
            product_id

        ))

        connection.commit()


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

        connection.execute("""
            DELETE FROM products
            WHERE id = ?
        """, (
            product_id,
        ))

        connection.commit()


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

        connection.execute("""
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

        """, (

            order_id,
            product_id,
            product_name,
            customer_name,
            phone,
            quantity,
            unit_price,
            total_price

        ))

        connection.commit()


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

        order = connection.execute("""
            SELECT *
            FROM orders
            WHERE order_id = ?
        """, (
            order_id,
        )).fetchone()

        return order


    finally:

        connection.close()


# ==========================================
# GET ALL ORDERS
# ==========================================

def get_all_orders():

    connection = get_connection()

    try:

        orders = connection.execute("""
            SELECT *
            FROM orders
            ORDER BY id DESC
        """).fetchall()

        return orders


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

        connection.execute("""
            UPDATE orders
            SET status = ?
            WHERE order_id = ?
        """, (
            status,
            order_id
        ))

        connection.commit()


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

        connection.execute("""
            DELETE FROM orders
            WHERE order_id = ?
        """, (
            order_id,
        ))

        connection.commit()


    finally:

        connection.close()