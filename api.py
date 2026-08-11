from flask import Flask, jsonify
from config import PORT, DEBUG
from admin import get_drivers, approve_driver, reject_driver

from auth import (
    register_passenger,
    login_passenger,
    register_driver,
    login_driver
)

app = Flask(__name__)


@app.get("/")
def home():
    return jsonify({
        "success": True,
        "service": "TaxiServer",
        "version": "1.0.0",
        "status": "online"
    })


@app.get("/health")
def health():
    return jsonify({
        "success": True,
        "status": "healthy"
    })


@app.post("/auth/passenger/register")
def auth_passenger_register():
    return register_passenger()


@app.post("/auth/passenger/login")
def auth_passenger_login():
    return login_passenger()


@app.post("/auth/driver/register")
def auth_driver_register():
    return register_driver()


@app.post("/auth/driver/login")
def auth_driver_login():
    return login_driver()


@app.get("/admin/drivers")
def admin_drivers():
    return get_drivers()


@app.post("/admin/drivers/<int:driver_id>/approve")
def admin_approve_driver(driver_id):
    return approve_driver(driver_id)


@app.post("/admin/drivers/<int:driver_id>/reject")
def admin_reject_driver(driver_id):
    return reject_driver(driver_id)


@app.get("/api")
def api_info():
    return jsonify({
        "success": True,
        "service": "Taxi API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "passenger": "/passenger",
            "driver": "/driver",
            "orders": "/orders",
            "admin": "/admin"
        }
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=DEBUG
    )
