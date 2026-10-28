import mysql.connector
from flask import Flask, jsonify, request

from common.db import init_db, list_parts, get_part, create_part, update_part, delete_part

app = Flask(__name__)


def validate_part(data):
    if not isinstance(data, dict):
        return "Request body must be a JSON object"
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        return "name must be a non-empty string"
    if not isinstance(data.get("sku"), str) or not data["sku"].strip():
        return "sku must be a non-empty string"
    if type(data.get("quantity")) is not int or data["quantity"] < 0:
        return "quantity must be a non-negative integer"
    price = data.get("price")
    if type(price) not in (int, float) or price < 0:
        return "price must be a non-negative number"
    return None


def normalized(data):
    data["name"] = data["name"].strip()
    data["sku"] = data["sku"].strip()
    return data


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/parts")
def all_parts():
    return jsonify(list_parts()), 200


@app.get("/parts/<int:part_id>")
def one_part(part_id):
    part = get_part(part_id)
    if part is None:
        return jsonify({"error": "Part not found"}), 404
    return jsonify(part), 200


@app.post("/parts")
def add_part():
    data = request.get_json(silent=True)
    error = validate_part(data)
    if error:
        return jsonify({"error": error}), 400
    try:
        part = create_part(normalized(data))
    except mysql.connector.IntegrityError:
        return jsonify({"error": "SKU already exists or data violates a database constraint"}), 409
    return jsonify(part), 201


@app.put("/parts/<int:part_id>")
def replace_part(part_id):
    data = request.get_json(silent=True)
    error = validate_part(data)
    if error:
        return jsonify({"error": error}), 400
    try:
        part = update_part(part_id, normalized(data))
    except mysql.connector.IntegrityError:
        return jsonify({"error": "SKU already exists or data violates a database constraint"}), 409
    if part is None:
        return jsonify({"error": "Part not found"}), 404
    return jsonify(part), 200


@app.delete("/parts/<int:part_id>")
def remove_part(part_id):
    if not delete_part(part_id):
        return "", 404
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=4949, debug=False)
