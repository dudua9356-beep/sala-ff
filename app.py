from flask import Flask, render_template, request, redirect, url_for, session
import mercadopago
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "minha_chave_secreta")  # usado pra sessão ADM

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Configuração das salas
SALAS = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "max_vagas": 49, "jogadores": []},
    "Sala 2": {"id": "654321", "senha": "ghijkl", "max_vagas": 49, "jogadores": []},
}

# Senha do ADM
ADM_SENHA = "Duduzin321@"


# ===================== ROTAS =====================

@app.route("/", methods=["GET", "POST"])
def home():
    erro = None
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_escolhida = request.form.get("sala")
        if not nick:
            erro = "Digite seu nick do Free Fire."
        elif sala_escolhida not in SALAS:
            erro = "Sala inválida."
        elif len(SALAS[sala_escolhida]["jogadores"]) >= SALAS[sala_escolhida]["max_vagas"]:
            erro = "Essa sala está lotada."
        else:
            return redirect(url_for("pago", nick=nick, sala=sala_escolhida))
    return render_template("index.html", salas=SALAS, erro=erro)


@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala or sala not in SALAS:
        return redirect(url_for("home"))

    # Criar pagamento no Mercado Pago (PIX)
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala} - Free Fire",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"},
    }

    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    pix_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")

    return render_template("pago.html", nick=nick, sala=sala, qr_code=qr_code, pix_code=pix_code)


@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala or sala not in SALAS:
        return redirect(url_for("home"))

    if nick not in SALAS[sala]["jogadores"]:
        SALAS[sala]["jogadores"].append(nick)

    sala_info = SALAS[sala]
    return render_template("sala.html", nick=nick, id_sala=sala_info["id"], senha=sala_info["senha"])


# ===================== PAINEL ADM =====================

@app.route("/adm", methods=["GET", "POST"])
def adm_login():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADM_SENHA:
            session["adm_logged_in"] = True
            return redirect(url_for("admin_panel"))
        else:
            erro = "Senha incorreta."
    return render_template("admin_login.html", erro=erro)


@app.route("/admin")
def admin_panel():
    if not session.get("adm_logged_in"):
        return redirect(url_for("adm_login"))
    return render_template("admin.html", salas=SALAS)


@app.route("/logout")
def logout():
    session.pop("adm_logged_in", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
