from flask import Flask, request, jsonify, render_template
import mercadopago
import sqlite3
import os

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

sdk = mercadopago.SDK(ACCESS_TOKEN)

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nick TEXT,
            payment_id TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/criar_pagamento", methods=["POST"])
def criar_pagamento():
    data = request.json
    nick = data["nick"]

    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Inscrição Sala FF - {nick}",
        "payment_method_id": "pix",
        "payer": {
            "email": "teste@test.com"
        }
    }

    payment = sdk.payment().create(payment_data)["response"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO jogadores (nick, payment_id, status) VALUES (?, ?, ?)",
              (nick, payment["id"], "pendente"))
    conn.commit()
    conn.close()

    return jsonify({
        "qr_code": payment["point_of_interaction"]["transaction_data"]["qr_code_base64"],
        "payment_id": payment["id"]
    })

@app.route("/verificar/<payment_id>")
def verificar(payment_id):
    payment = sdk.payment().get(payment_id)["response"]
    status = payment["status"]

    if status == "approved":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE jogadores SET status = 'aprovado' WHERE payment_id = ?", (payment_id,))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "aprovado",
            "sala_id": "123456",
            "senha": "SOUZAX"
        })

    return jsonify({"status": "pendente"})

if __name__ == "__main__":
    app.run()
