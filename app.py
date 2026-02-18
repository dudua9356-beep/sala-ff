from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # coloque no Render
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Dicionário de salas
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "max": 49, "jogadores": []},
    "Sala 2": {"id": "654321", "senha": "fedcba", "max": 49, "jogadores": []},
}

# Senha do painel ADM
ADM_SENHA = "Duduzin321@"


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_nome = request.form.get("sala")
        if not nick or not sala_nome:
            return render_template("index.html", erro="Digite seu nick e escolha a sala.", salas=salas)
        return redirect(url_for("pago", nick=nick, sala=sala_nome))
    return render_template("index.html", salas=salas)


@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")
    if not nick or not sala_nome:
        return redirect(url_for("home"))

    # Criar pagamento PIX
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala_nome} 🔥",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"},
    }
    payment = sdk.payment().create(payment_data)
    qr_code_base64 = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    qr_code_text = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")

    # Salvar jogador temporariamente
    salas[sala_nome]["jogadores"].append({"nick": nick, "pago": False})

    return render_template(
        "pago.html",
        nick=nick,
        sala_nome=sala_nome,
        qr_code_base64=qr_code_base64,
        qr_code_text=qr_code_text,
        salas=salas
    )


@app.route("/check_payment")
def check_payment():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")
    # Checa se pagamento confirmado
    for jogador in salas[sala_nome]["jogadores"]:
        if jogador["nick"] == nick:
            # Aqui você pode integrar com Mercado Pago para checar status real
            # Por enquanto vamos simular como pago automático
            jogador["pago"] = True
            return {"status": "pago", "id": salas[sala_nome]["id"], "senha": salas[sala_nome]["senha"]}
    return {"status": "aguardando"}


@app.route("/adm_login", methods=["GET", "POST"])
def adm_login():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADM_SENHA:
            return redirect(url_for("adm_panel"))
        else:
            return render_template("adm_login.html", erro="Senha incorreta!")
    return render_template("adm_login.html")


@app.route("/adm_panel")
def adm_panel():
    return render_template("admin.html", salas=salas)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
