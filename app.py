from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os
import json

app = Flask(__name__)

# =======================
# CONFIGURAÇÃO MERCADO PAGO
# =======================
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # coloque no Render
sdk = mercadopago.SDK(ACCESS_TOKEN)

# =======================
# ID e senha da sala
# =======================
SALA_ID = os.environ.get("SALA_ID", "123456")      # você pode mudar no Render
SALA_SENHA = os.environ.get("SALA_SENHA", "abcdef") # você pode mudar no Render

# =======================
# Jogadores que pagaram
# =======================
# Vai salvar em arquivo simples para não perder se o app reiniciar
PAGAMENTOS_FILE = "pagamentos.json"

def carregar_pagamentos():
    if os.path.exists(PAGAMENTOS_FILE):
        with open(PAGAMENTOS_FILE, "r") as f:
            return json.load(f)
    return []

def salvar_pagamentos(jogadores):
    with open(PAGAMENTOS_FILE, "w") as f:
        json.dump(jogadores, f)

jogadores_pagaram = carregar_pagamentos()

# =======================
# Rota principal - Formulário Nick
# =======================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        if not nick:
            return render_template("index.html", erro="Digite seu nick do Free Fire.")
        return redirect(url_for("pago", nick=nick))
    return render_template("index.html")

# =======================
# Página de pagamento PIX
# =======================
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    if not nick:
        return redirect(url_for("home"))

    # Criar pagamento no Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": "Recarga Sala FF 🔥",
        "payment_method_id": "pix",
        "payer": {
            "email": f"{nick}@exemplo.com"
        }
    }

    payment = sdk.payment().create(payment_data)

    # Pega QR code base64
    qr_code_base64 = payment["response"]["point_of_interaction"]["transaction_data"].get("qr_code_base64", "")
    qr_code = f"data:image/png;base64,{qr_code_base64}"

    # Salva jogador temporariamente (vai liberar sala só depois de aprovar)
    if nick not in jogadores_pagaram:
        jogadores_pagaram.append({"nick": nick, "status": "pending"})
        salvar_pagamentos(jogadores_pagaram)

    return render_template("pago.html", nick=nick, qr_code=qr_code)

# =======================
# Página da sala - só libera se pagou
# =======================
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    if not nick:
        return redirect(url_for("home"))

    # Checa se jogador pagou
    pagou = False
    for j in jogadores_pagaram:
        if j["nick"] == nick and j.get("status") == "approved":
            pagou = True
            break

    if not pagou:
        return redirect(url_for("home"))

    return render_template("sala.html", id_sala=SALA_ID, senha=SALA_SENHA, nick=nick)

# =======================
# Webhook para atualizar status do pagamento (opcional)
# =======================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "No data", 400

    # Exemplo de atualização: quando Mercado Pago aprovar pagamento
    payment_id = data.get("id")
    if not payment_id:
        return "No payment ID", 400

    payment = sdk.payment().get(payment_id)
    status = payment["response"]["status"]

    # Atualiza lista de jogadores
    nick = payment["response"]["payer"]["email"].split("@")[0]
    for j in jogadores_pagaram:
        if j["nick"] == nick:
            j["status"] = status
            break
    salvar_pagamentos(jogadores_pagaram)

    return "OK", 200

# =======================
# RUN
# =======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
