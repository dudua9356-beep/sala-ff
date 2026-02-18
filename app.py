from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # Configure no Render com seu Access Token
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Configurações da sala
SALA_ID = "123456"       # Mude aqui ou mantenha fixo
SALA_SENHA = "abcdef"    # Mude aqui ou mantenha fixo
MAX_JOGADORES = 49

# Lista de jogadores que já pagaram
jogadores_pagaram = []

# Salas disponíveis (para exibir na página inicial)
salas = {
    "Sala 1": {"id": SALA_ID, "senha": SALA_SENHA, "ocupados": 0, "max": MAX_JOGADORES}
}

# Rota principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_escolhida = request.form.get("sala")
        if not nick:
            return render_template("index.html", salas=salas, erro="Digite seu nick do Free Fire.")
        if sala_escolhida not in salas:
            return render_template("index.html", salas=salas, erro="Sala inválida.")
        # Verifica se a sala está cheia
        if salas[sala_escolhida]["ocupados"] >= salas[sala_escolhida]["max"]:
            return render_template("index.html", salas=salas, erro="Sala lotada!")
        return redirect(url_for("pago", nick=nick, sala=sala_escolhida))
    return render_template("index.html", salas=salas)

# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala_escolhida = request.args.get("sala")
    if not nick or sala_escolhida not in salas:
        return redirect(url_for("home"))

    # Criar pagamento no Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala_escolhida} - {nick}",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"}  # só pra identificar o pagamento
    }

    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")

    # Adiciona jogador à lista e atualiza a sala
    if nick not in jogadores_pagaram:
        jogadores_pagaram.append(nick)
        salas[sala_escolhida]["ocupados"] += 1

    return render_template("pago.html", nick=nick, qr_code=qr_code, sala=sala_escolhida)

# Página da sala (após pagamento)
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala_escolhida = request.args.get("sala")
    if nick not in jogadores_pagaram or sala_escolhida not in salas:
        return redirect(url_for("home"))

    id_sala = salas[sala_escolhida]["id"]
    senha_sala = salas[sala_escolhida]["senha"]

    return render_template("sala.html", nick=nick, id_sala=id_sala, senha_sala=senha_sala)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
