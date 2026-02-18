from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Salas disponíveis
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef"},
    "Sala 2": {"id": "654321", "senha": "ghijkl"}
}

# Lista de jogadores que já pagaram
jogadores_pagaram = []

# Página inicial
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        if not nick:
            return render_template("index.html", erro="Digite seu nick do Free Fire.", salas=salas)
        return redirect(url_for("pago", nick=nick))
    return render_template("index.html", salas=salas)

# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    if not nick:
        return redirect(url_for("home"))

    # Criar pagamento PIX no Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": "Recarga Sala FF 🔥",
        "payment_method_id": "pix",
        "payer": {
            "email": f"{nick}@exemplo.com"
        }
    }

    payment = sdk.payment().create(payment_data)
    qr_code_base64 = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")

    # Adiciona jogador à lista
    if nick not in jogadores_pagaram:
        jogadores_pagaram.append(nick)

    return render_template("pago.html", nick=nick, qr_code=qr_code_base64)

# Página da sala (mostra ID e senha)
@app.route("/sala/<nome_sala>")
def sala(nome_sala):
    nick = request.args.get("nick")
    if nick not in jogadores_pagaram or nome_sala not in salas:
        return redirect(url_for("home"))

    sala_info = salas[nome_sala]
    return render_template("sala.html", nick=nick, id_sala=sala_info["id"], senha=sala_info["senha"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
