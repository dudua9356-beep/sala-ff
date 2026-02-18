# app.py
import os
from flask import Flask, render_template, jsonify
import mercadopago

app = Flask(__name__)

# Recupera token do Mercado Pago da variável de ambiente
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "TEST-9be957f7-9594-49c3-bf6a-b475d798c4d9")

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# Rota da página inicial
@app.route("/")
def home():
    return render_template("index.html")

# Rota para criar pagamento
@app.route("/criar-pagamento")
def criar_pagamento():
    # Monta preferências do pagamento
    preference_data = {
        "items": [
            {
                "title": "Inscrição Sala FF",
                "quantity": 1,
                "unit_price": 6.0  # R$6
            }
        ],
        "back_urls": {
            "success": "https://sala-ff-2.onrender.com/sucesso",
            "failure": "https://sala-ff-2.onrender.com/falha",
            "pending": "https://sala-ff-2.onrender.com/pendente"
        },
        "auto_return": "approved"
    }

    preference_response = sdk.preference().create(preference_data)
    link_pagamento = preference_response["response"]["init_point"]

    return jsonify({"link_pagamento": link_pagamento})

# Rotas de exemplo para retorno do pagamento
@app.route("/sucesso")
def sucesso():
    return "Pagamento aprovado! Copie o ID da sala e a senha."

@app.route("/falha")
def falha():
    return "Pagamento não realizado."

@app.route("/pendente")
def pendente():
    return "Pagamento pendente."

# Rodando o app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
