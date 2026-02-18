from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # pegue do Render
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Dicionário de salas
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef"},
    "Sala 2": {"id": "654321", "senha": "ghijkl"}
}

# Lista de jogadores que já pagaram
jogadores_pagaram = []

# ADM senha
ADM_SENHA = "Duduzin321@"

# Rota principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_escolhida = request.form.get("sala")
        if not nick or not sala_escolhida:
            return render_template("index.html", salas=salas, erro="Preencha seu nick e escolha a sala.")
        return redirect(url_for("pago", nick=nick, sala=sala_escolhida))
    return render_template("index.html", salas=salas)

# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala:
        return redirect(url_for("home"))

    # Criar pagamento no Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala} - Free Fire 🔥",
        "payment_method_id": "pix",
        "payer": {
            "email": f"{nick}@exemplo.com"
        }
    }

    payment = sdk.payment().create(payment_data)
    qr_code_base64 = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    qr_code_text = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")

    # Adiciona jogador à lista
    if nick not in jogadores_pagaram:
        jogadores_pagaram.append({"nick": nick, "sala": sala, "pago": False})

    return render_template("pago.html", nick=nick, sala=sala, qr_code=qr_code_base64, qr_code_text=qr_code_text)

# Página da sala
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    jogador = next((j for j in jogadores_pagaram if j["nick"] == nick and j["sala"] == sala), None)
    if not jogador or not jogador["pago"]:
        return redirect(url_for("home"))

    sala_info = salas[sala]
    return render_template("sala.html", id_sala=sala_info["id"], senha=sala_info["senha"], nick=nick)

# Página ADM login
@app.route("/adm_login", methods=["GET", "POST"])
def adm_login():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADM_SENHA:
            return redirect(url_for("adm_panel"))
        else:
            erro = "Senha incorreta"
    return render_template("adm_login.html", erro=erro)

# Página ADM painel
@app.route("/adm_panel")
def adm_panel():
    return render_template("admin.html", salas=salas, jogadores=jogadores_pagaram)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
