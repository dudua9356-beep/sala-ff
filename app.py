from flask import Flask, render_template, request, redirect, url_for, flash
import mercadopago
import os

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Salas com ID e senha (editáveis via ADM)
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "jogadores": []},
    "Sala 2": {"id": "654321", "senha": "fedcba", "jogadores": []},
}

# Senha ADM
ADM_SENHA = "Duduzin321@"


# Página principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala = request.form.get("sala")
        if not nick or not sala:
            flash("Digite seu nick e selecione a sala.", "erro")
            return redirect(url_for("home"))
        return redirect(url_for("pago", nick=nick, sala=sala))
    return render_template("index.html", salas=salas)


# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala or sala not in salas:
        flash("Dados inválidos.", "erro")
        return redirect(url_for("home"))

    # Criar pagamento Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala} - Free Fire",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"},
    }

    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get(
        "transaction_data", {}
    ).get("qr_code_base64", "")
    pix_code = payment["response"].get("point_of_interaction", {}).get(
        "transaction_data", {}
    ).get("qr_code", "")

    # Adiciona jogador à lista temporária
    if nick not in salas[sala]["jogadores"]:
        salas[sala]["jogadores"].append({"nick": nick, "pago": False})

    return render_template("pago.html", nick=nick, sala=sala, qr_code=qr_code, pix_code=pix_code)


# Página da sala (após pagamento confirmado)
@app.route("/sala")
def sala_page():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala or sala not in salas:
        flash("Acesso inválido.", "erro")
        return redirect(url_for("home"))

    # Verifica se pagou
    jogador = next((j for j in salas[sala]["jogadores"] if j["nick"] == nick), None)
    if not jogador or not jogador["pago"]:
        flash("Pagamento não confirmado.", "erro")
        return redirect(url_for("home"))

    return render_template(
        "sala.html",
        nick=nick,
        id_sala=salas[sala]["id"],
        senha=salas[sala]["senha"],
        sala=sala,
    )


# Login ADM
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADM_SENHA:
            return redirect(url_for("admin_panel"))
        else:
            flash("Senha incorreta.", "erro")
    return render_template("admin_login.html")


# Painel ADM
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        sala = request.form.get("sala")
        id_sala = request.form.get("id_sala")
        senha_sala = request.form.get("senha_sala")
        if sala in salas:
            salas[sala]["id"] = id_sala
            salas[sala]["senha"] = senha_sala
            flash("Sala atualizada com sucesso!", "success")
    return render_template("admin.html", salas=salas)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
