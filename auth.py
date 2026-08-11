import hashlib
import secrets
import time

from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash


passengers = {}
drivers = {}

_tokens = {}


def _new_token(user_type, user_id):
    token = secrets.token_urlsafe(32)

    _tokens[token] = {
        "type": user_type,
        "id": user_id,
        "created_at": time.time()
    }

    return token


def _json():
    return request.get_json(silent=True) or {}


def register_passenger():
    data = _json()

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not name or not phone or not password:
        return jsonify({
            "success": False,
            "message": "Ism, telefon va parol kerak"
        }), 400

    if len(password) < 4:
        return jsonify({
            "success": False,
            "message": "Parol kamida 4 ta belgidan iborat bo‘lsin"
        }), 400

    if phone in passengers:
        return jsonify({
            "success": False,
            "message": "Bu telefon raqami allaqachon ro‘yxatdan o‘tgan"
        }), 409

    user_id = len(passengers) + 1

    passengers[phone] = {
        "id": user_id,
        "name": name,
        "phone": phone,
        "password_hash": generate_password_hash(password)
    }

    return jsonify({
        "success": True,
        "message": "Yo‘lovchi muvaffaqiyatli ro‘yxatdan o‘tdi",
        "user": {
            "id": user_id,
            "name": name,
            "phone": phone
        }
    }), 201


def login_passenger():
    data = _json()

    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    user = passengers.get(phone)

    if not user or not check_password_hash(
        user["password_hash"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Telefon yoki parol noto‘g‘ri"
        }), 401

    token = _new_token("passenger", user["id"])

    return jsonify({
        "success": True,
        "message": "Login muvaffaqiyatli",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "phone": user["phone"]
        }
    })


def register_driver():
    data = _json()

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    login = str(data.get("login", "")).strip()
    password = str(data.get("password", ""))
    car_model = str(data.get("car_model", "")).strip()
    car_number = str(data.get("car_number", "")).strip()

    if not all([
        name,
        phone,
        login,
        password,
        car_model,
        car_number
    ]):
        return jsonify({
            "success": False,
            "message": "Barcha maydonlarni kiriting"
        }), 400

    if len(password) < 4:
        return jsonify({
            "success": False,
            "message": "Parol kamida 4 ta belgidan iborat bo‘lsin"
        }), 400

    for driver in drivers.values():
        if driver["phone"] == phone:
            return jsonify({
                "success": False,
                "message": "Bu telefon raqami band"
            }), 409

        if driver["login"].lower() == login.lower():
            return jsonify({
                "success": False,
                "message": "Bu login band"
            }), 409

    driver_id = len(drivers) + 1

    drivers[driver_id] = {
        "id": driver_id,
        "name": name,
        "phone": phone,
        "login": login,
        "password_hash": generate_password_hash(password),
        "car_model": car_model,
        "car_number": car_number,
        "approved": False,
        "online": False,
        "balance": 0
    }

    return jsonify({
        "success": True,
        "message": "Haydovchi ro‘yxatdan o‘tdi. Admin tasdig‘i kutilmoqda.",
        "driver": {
            "id": driver_id,
            "name": name,
            "phone": phone,
            "login": login,
            "car_model": car_model,
            "car_number": car_number,
            "approved": False,
            "online": False
        }
    }), 201


def login_driver():
    data = _json()

    login = str(data.get("login", "")).strip()
    password = str(data.get("password", ""))

    driver = None

    for item in drivers.values():
        if item["login"].lower() == login.lower():
            driver = item
            break

    if not driver or not check_password_hash(
        driver["password_hash"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Login yoki parol noto‘g‘ri"
        }), 401

    if not driver["approved"]:
        return jsonify({
            "success": False,
            "message": "Admin hali haydovchini tasdiqlamagan"
        }), 403

    token = _new_token("driver", driver["id"])

    return jsonify({
        "success": True,
        "message": "Login muvaffaqiyatli",
        "token": token,
        "driver": {
            "id": driver["id"],
            "name": driver["name"],
            "phone": driver["phone"],
            "login": driver["login"],
            "car_model": driver["car_model"],
            "car_number": driver["car_number"],
            "approved": driver["approved"],
            "online": driver["online"],
            "balance": driver["balance"]
        }
    })


def get_token_data():
    header = request.headers.get("Authorization", "")

    if not header.startswith("Bearer "):
        return None

    token = header[7:].strip()

    return _tokens.get(token)
