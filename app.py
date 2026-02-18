import os
import mercadopago
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Pegando o Access Token da variável de ambiente
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/criar-pagamento")
def criar_pagamento():
    preference_data = {
        "items": [
            {
                "title": "Recarga Sala FF",
                "quantity": 1,
                "unit_price": 10.0
            }
        ]
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    return jsonify({
        "link_pagamento": preference["init_point"]
    })

if __name__ == "__main__":
    app.run(debug=True)
