from flask import Flask, render_template, request, redirect, url_for, session
import mercadopago
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # necessário para sessões

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Lista de jogadores que já pagaram
jogadores_pagaram = []

# Salas disponíveis
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "ocupados": 0, "max": 49},
    "Sala 2": {"id": "654321", "senha": "fedcba", "ocupados": 0, "max": 49},
}

# Senha do painel ADM
ADM_PASSWORD = "Duduzin321@"


# Rota principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala = request.form.get("sala")
        if not nick or not sala:
            return render_template("index.html", erro="Preencha nick e sala", salas=salas)

        # Verifica se a sala existe e se não está cheia
        if sala not in salas:
            return render_template("index.html", erro="Sala inválida", salas=salas)
        if salas[sala]["ocupados"] >= salas[sala]["max"]:
            return render_template("index.html", erro="Sala lotada", salas=salas)

        return redirect(url_for("pago", nick=nick, sala=sala))

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
        "description": f"Recarga {sala} - {nick}",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"}
    }

    payment = sdk.payment().create(payment_data)
    payment_url = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")

    # Adiciona jogador à lista
    if nick not in jogadores_pagaram:
        jogadores_pagaram.append({"nick": nick, "sala": sala})
        salas[sala]["ocupados"] += 1

    return render_template("pago.html", nick=nick, sala=sala, qr_code=payment_url)


# Página da sala
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala = request.args.get("sala")

    if not nick or not sala:
        return redirect(url_for("home"))

    jogador = next((j for j in jogadores_pagaram if j["nick"] == nick and j["sala"] == sala), None)
    if not jogador:
        return redirect(url_for("home"))

    sala_info = salas.get(sala)
    return render_template("sala.html", id_sala=sala_info["id"], senha=sala_info["senha"], nick=nick)


# Painel ADM
@app.route("/adm", methods=["GET", "POST"])
def adm():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADM_PASSWORD:
            session["adm"] = True
            return redirect(url_for("painel"))
        else:
            return render_template("adm_login.html", erro="Senha incorreta")

    return render_template("adm_login.html")


@app.route("/painel")
def painel():
    if not session.get("adm"):
        return redirect(url_for("adm"))

    return render_template("painel.html", salas=salas, jogadores=jogadores_pagaram)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
