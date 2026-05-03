from flask import Flask, render_template, request, redirect, url_for, jsonify
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Salas
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "ocupados": 0, "max": 49},
    "Sala 2": {"id": "654321", "senha": "fedcba", "ocupados": 0, "max": 49}
}

# Jogadores
jogadores_pagaram = []

SENHA_ADM = "Duduzin321@"

# ------------------- HOME -------------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_escolhida = request.form.get("sala")

        if not nick:
            return render_template("index.html", erro="Digite seu nick.", salas=salas)

        if sala_escolhida not in salas:
            return render_template("index.html", erro="Sala inválida.", salas=salas)

        # BLOQUEIA SE LOTOU
        if salas[sala_escolhida]["ocupados"] >= salas[sala_escolhida]["max"]:
            return render_template("index.html", erro="Sala já está cheia.", salas=salas)

        return redirect(url_for("pago", nick=nick, sala=sala_escolhida))

    return render_template("index.html", salas=salas)

# ------------------- PAGAMENTO -------------------
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")

    if not nick or sala_nome not in salas:
        return redirect(url_for("home"))

    # Evita duplicar jogador
    existente = next((j for j in jogadores_pagaram if j["nick"] == nick and j["sala"] == sala_nome), None)
    if not existente:
        jogadores_pagaram.append({
            "nick": nick,
            "sala": sala_nome,
            "pago": False
        })

    # Cria pagamento PIX
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala_nome}",
        "payment_method_id": "pix",
        "external_reference": f"{nick}|{sala_nome}",
        "payer": {
            "email": f"{nick}@exemplo.com"
        }
    }

    payment = sdk.payment().create(payment_data)

    qr_base64 = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"]
    qr_code = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code"]

    return render_template(
        "pago.html",
        nick=nick,
        qr_code=qr_base64,
        qr_code_text=qr_code,
        sala=sala_nome
    )

# ------------------- SALA -------------------
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")

    jogador = next((j for j in jogadores_pagaram if j["nick"] == nick and j["sala"] == sala_nome), None)

    if not jogador or not jogador["pago"]:
        return redirect(url_for("home"))

    sala_info = salas[sala_nome]

    return render_template(
        "sala.html",
        id_sala=sala_info["id"],
        senha=sala_info["senha"],
        nick=nick,
        sala=sala_nome
    )

# ------------------- STATUS (AJAX) -------------------
@app.route("/status")
def status():
    nick = request.args.get("nick")
    sala = request.args.get("sala")

    jogador = next((j for j in jogadores_pagaram if j["nick"] == nick and j["sala"] == sala), None)

    return jsonify({"pago": jogador["pago"] if jogador else False})

# ------------------- WEBHOOK REAL -------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data and data.get("type") == "payment":
        payment_id = data["data"]["id"]

        payment = sdk.payment().get(payment_id)
        status = payment["response"]["status"]

        if status == "approved":
            ref = payment["response"].get("external_reference", "")
            if "|" in ref:
                nick, sala_nome = ref.split("|")

                jogador = next(
                    (j for j in jogadores_pagaram if j["nick"] == nick and j["sala"] == sala_nome),
                    None
                )

                if jogador and not jogador["pago"]:
                    if salas[sala_nome]["ocupados"] < salas[sala_nome]["max"]:
                        jogador["pago"] = True
                        salas[sala_nome]["ocupados"] += 1
                    else:
                        print("Sala cheia - considerar reembolso")

    return "OK", 200

# ------------------- ADM -------------------
@app.route("/adm_login", methods=["GET", "POST"])
def adm_login():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == SENHA_ADM:
            return redirect(url_for("admin"))
        else:
            erro = "Senha incorreta."
    return render_template("admin_login.html", erro=erro)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        sala_nome = request.form.get("sala")
        novo_id = request.form.get("id_sala")
        nova_senha = request.form.get("senha_sala")

        if sala_nome in salas:
            salas[sala_nome]["id"] = novo_id
            salas[sala_nome]["senha"] = nova_senha

    return render_template("admin.html", salas=salas, jogadores=jogadores_pagaram)

# ------------------- RUN -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
