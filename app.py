from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # coloque seu token aqui no Render
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Salas iniciais
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "ocupados": 0, "max": 49},
    "Sala 2": {"id": "654321", "senha": "fedcba", "ocupados": 0, "max": 49}
}

# Lista de jogadores que já pagaram
jogadores_pagaram = []

# Senha ADM
SENHA_ADM = "Duduzin321@"

# ------------------- ROTAS -------------------

# Home
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_escolhida = request.form.get("sala")
        if not nick:
            return render_template("index.html", erro="Digite seu nick do Free Fire.", salas=salas)
        if sala_escolhida not in salas:
            return render_template("index.html", erro="Escolha uma sala válida.", salas=salas)
        return redirect(url_for("pago", nick=nick, sala=sala_escolhida))
    return render_template("index.html", salas=salas)

# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")

    if not nick or sala_nome not in salas:
        return redirect(url_for("home"))

    # Criação do pagamento
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala_nome}",
        "payment_method_id": "pix",
        "payer": {
            "email": f"{nick}@exemplo.com"
        }
    }

    payment = sdk.payment().create(payment_data)
    payment_url = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    payment_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")

    # Adiciona jogador à lista temporária
    if nick not in jogadores_pagaram:
        jogadores_pagaram.append({"nick": nick, "sala": sala_nome, "pago": False})

    return render_template("pago.html", nick=nick, qr_code=payment_url, qr_code_text=payment_code, sala=sala_nome)

# Página da sala
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")
    jogador = next((j for j in jogadores_pagaram if j["nick"] == nick and j["sala"] == sala_nome), None)
    if not jogador or not jogador["pago"]:
        return redirect(url_for("home"))

    sala_info = salas[sala_nome]
    return render_template("sala.html", id_sala=sala_info["id"], senha=sala_info["senha"], nick=nick, sala=sala_nome)

# Login ADM
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

# Painel ADM
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

# Atualiza pagamento (simulação)
@app.route("/confirmar_pagamento")
def confirmar_pagamento():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")
    jogador = next((j for j in jogadores_pagaram if j["nick"] == nick and j["sala"] == sala_nome), None)
    if jogador:
        jogador["pago"] = True
        salas[sala_nome]["ocupados"] += 1
    return redirect(url_for("sala", nick=nick, sala=sala_nome))

# ------------------- RODA O FLASK -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
