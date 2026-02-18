from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # pegue do Render
sdk = mercadopago.SDK(ACCESS_TOKEN)

# ID e senha da sala
SALA_ID = "123456"
SALA_SENHA = "abcdef"

# Lista de jogadores que já pagaram
jogadores_pagaram = []

# Senha do painel ADM
ADM_SENHA = "Duduzin321@"

# -------------------- ROTAS --------------------

# Rota principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        if not nick:
            return render_template("index.html", erro="Digite seu nick do Free Fire.")
        return redirect(url_for("pago", nick=nick))
    return render_template("index.html")

# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    if not nick:
        return redirect(url_for("home"))

    # Criar pagamento PIX no Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga Sala FF 🔥 - {nick}",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"}
    }

    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    pix_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")

    return render_template("pago.html", nick=nick, qr_code=qr_code, payment_code=pix_code)

# Página da sala
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    if nick not in jogadores_pagaram:
        return redirect(url_for("home"))

    return render_template("sala.html", id_sala=SALA_ID, senha=SALA_SENHA, nick=nick)

# -------------------- PAINEL ADM --------------------

@app.route("/adm", methods=["GET", "POST"])
def adm():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADM_SENHA:
            return render_template("admin.html", jogadores=jogadores_pagaram,
                                   sala_id=SALA_ID, sala_senha=SALA_SENHA)
        else:
            return render_template("admin_login.html", erro="Senha incorreta!")
    return render_template("admin_login.html")

# -------------------- CONFIRMAÇÃO DE PAGAMENTO --------------------

@app.route("/confirmar_pagamento", methods=["POST"])
def confirmar_pagamento():
    nick = request.form.get("nick")
    if nick and nick not in jogadores_pagaram:
        jogadores_pagaram.append(nick)
        return {"status": "ok", "message": f"Pagamento confirmado para {nick}."}
    return {"status": "erro", "message": "Jogador já confirmado ou inválido."}

# -------------------- EXECUÇÃO --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
