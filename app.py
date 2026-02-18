from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Lista de salas (ID, senha e ocupação)
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "ocupadas": 0, "max": 49},
    "Sala 2": {"id": "654321", "senha": "ghijkl", "ocupadas": 0, "max": 49},
}

# Lista de jogadores que já pagaram
jogadores_pagaram = {}

# Senha do painel ADM
SENHA_ADM = "Duduzin321@"


# Página inicial
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_escolhida = request.form.get("sala")
        if not nick or not sala_escolhida:
            return render_template("index.html", erro="Preencha todos os campos.", salas=salas)
        return redirect(url_for("pago", nick=nick, sala=sala_escolhida))
    return render_template("index.html", salas=salas)


# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala_escolhida = request.args.get("sala")
    if not nick or not sala_escolhida:
        return redirect(url_for("home"))

    # Checar se sala está cheia
    if salas[sala_escolhida]["ocupadas"] >= salas[sala_escolhida]["max"]:
        return render_template("pago.html", erro="Sala lotada.", nick=nick, sala=sala_escolhida)

    # Criar pagamento no Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala_escolhida} Free Fire 🔥",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"}
    }

    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    codigo_pix = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")

    return render_template("pago.html", nick=nick, sala=sala_escolhida, qr_code=qr_code, codigo_pix=codigo_pix)


# Página da sala após pagamento
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala_escolhida = request.args.get("sala")
    if not nick or sala_escolhida not in jogadores_pagaram or nick not in jogadores_pagaram[sala_escolhida]:
        return redirect(url_for("home"))

    return render_template("sala.html", id_sala=salas[sala_escolhida]["id"],
                           senha=salas[sala_escolhida]["senha"], nick=nick)


# Login do ADM
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == SENHA_ADM:
            return redirect(url_for("admin"))
        else:
            return render_template("admin_login.html", erro="Senha incorreta.")
    return render_template("admin_login.html")


# Painel ADM
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        # Atualizar salas
        for nome, dados in salas.items():
            salas[nome]["id"] = request.form.get(f"id_{nome}")
            salas[nome]["senha"] = request.form.get(f"senha_{nome}")
        return render_template("admin.html", salas=salas, sucesso="Salas atualizadas com sucesso!")
    return render_template("admin.html", salas=salas)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
