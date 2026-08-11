from flask import request, jsonify

from config import ADMIN_API_KEY
from auth import drivers


def check_admin():
    key = request.headers.get("X-Admin-Key", "")

    if not ADMIN_API_KEY or key != ADMIN_API_KEY:
        return False

    return True


def get_drivers():
    if not check_admin():
        return jsonify({
            "success": False,
            "message": "Admin ruxsati rad etildi"
        }), 401

    result = []

    for driver in drivers.values():
        result.append({
            "id": driver["id"],
            "name": driver["name"],
            "phone": driver["phone"],
            "login": driver["login"],
            "car_model": driver["car_model"],
            "car_number": driver["car_number"],
            "approved": driver["approved"],
            "online": driver["online"],
            "balance": driver["balance"]
        })

    return jsonify({
        "success": True,
        "drivers": result
    })


def approve_driver(driver_id):
    if not check_admin():
        return jsonify({
            "success": False,
            "message": "Admin ruxsati rad etildi"
        }), 401

    try:
        driver_id = int(driver_id)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Driver ID noto‘g‘ri"
        }), 400

    driver = drivers.get(driver_id)

    if not driver:
        return jsonify({
            "success": False,
            "message": "Haydovchi topilmadi"
        }), 404

    driver["approved"] = True

    return jsonify({
        "success": True,
        "message": "Haydovchi tasdiqlandi",
        "driver": {
            "id": driver["id"],
            "name": driver["name"],
            "approved": True
        }
    })


def reject_driver(driver_id):
    if not check_admin():
        return jsonify({
            "success": False,
            "message": "Admin ruxsati rad etildi"
        }), 401

    try:
        driver_id = int(driver_id)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Driver ID noto‘g‘ri"
        }), 400

    driver = drivers.get(driver_id)

    if not driver:
        return jsonify({
            "success": False,
            "message": "Haydovchi topilmadi"
        }), 404

    driver["approved"] = False
    driver["online"] = False

    return jsonify({
        "success": True,
        "message": "Haydovchi rad etildi"
    })
