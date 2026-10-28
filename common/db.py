
import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import IntegrityError

# Load environment variables from the project's .env file
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "connection_timeout": 10,
    # Enable TLS for your remote MySQL connection.
    "ssl_disabled": False,
}


def get_connection():
    """Create a connection to the configured MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Create the parts table if it doesn't already exist."""
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                sku VARCHAR(50) NOT NULL UNIQUE,
                quantity INT NOT NULL CHECK (quantity >= 0),
                price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def list_parts():
    """Return all parts."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT id, name, sku, quantity, price, created_at
                FROM parts
                ORDER BY id
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()


def get_part(part_id):
    """Return one part by ID, or None if it doesn't exist."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT id, name, sku, quantity, price, created_at
                FROM parts
                WHERE id = %s
            """, (part_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
    finally:
        connection.close()


def create_part(data):
    """Insert a part and return the newly created record."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO parts (name, sku, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (
                data["name"],
                data["sku"],
                data["quantity"],
                data["price"],
            ))
            part_id = cursor.lastrowid
            connection.commit()
        finally:
            cursor.close()

        return get_part(part_id)

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_part(part_id, data):
    """Update a part; return None if the ID doesn't exist."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                UPDATE parts
                SET name = %s, sku = %s, quantity = %s, price = %s
                WHERE id = %s
            """, (
                data["name"],
                data["sku"],
                data["quantity"],
                data["price"],
                part_id,
            ))
            changed = cursor.rowcount
            connection.commit()
        finally:
            cursor.close()

        # MySQL may report zero changed rows if values were unchanged.
        if changed == 0:
            return get_part(part_id)

        return get_part(part_id)

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def delete_part(part_id):
    """Delete a part; return True if it existed and was deleted."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM parts WHERE id = %s",
                (part_id,),
            )
            deleted = cursor.rowcount > 0
            connection.commit()
            return deleted
        finally:
            cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
