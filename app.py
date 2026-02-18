from flask import Flask, render_template, request, redirect, url_for, flash
import mercadopago
import os

app = Flask(__name__)
app.secret_key = "supersecreto123"

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # coloque no Render
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Salas
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "max_vagas": 49, "jogadores": []},
    "Sala 2": {"id": "654321", "senha": "fedcba", "max_vagas": 49, "jogadores": []},
}

# Lista de jogadores que já pagaram
pagamentos_confirmados = {}

# ADM
ADM_SENHA = "Duduzin321@"


# Rota principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_escolhida = request.form.get("sala")
        if not nick or not sala_escolhida:
            flash("Preencha nick e escolha uma sala")
            return redirect(url_for("home"))
        return redirect(url_for("pago", nick=nick, sala=sala_escolhida))
    return render_template("index.html", salas=salas)


# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")
    if not nick or not sala_nome:
        return redirect(url_for("home"))

    sala = salas.get(sala_nome)
    if not sala:
        flash("Sala inválida")
        return redirect(url_for("home"))

    # Checa se sala lotada
    if len(sala["jogadores"]) >= sala["max_vagas"]:
        return render_template("pago.html", erro="Sala lotada", nick=nick, sala_nome=sala_nome)

    # Cria pagamento Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala_nome} 🔥",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"},
    }

    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    pix_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")

    # Guarda o pagamento pendente
    pagamentos_confirmados[nick] = {"sala": sala_nome, "qr_code": qr_code, "pix_code": pix_code, "pago": False}

    return render_template("pago.html", nick=nick, sala_nome=sala_nome, qr_code=qr_code, pix_code=pix_code)


# Verifica pagamento e libera sala
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    if not nick or nick not in pagamentos_confirmados:
        return redirect(url_for("home"))

    pagamento = pagamentos_confirmados[nick]

    # Atualiza status do pagamento (simulação para testes)
    # No ambiente real, precisa de webhook do Mercado Pago para atualizar
    pagamento["pago"] = True
    sala_nome = pagamento["sala"]
    sala = salas[sala_nome]

    # Adiciona jogador na sala
    if nick not in sala["jogadores"]:
        sala["jogadores"].append(nick)

    return render_template("sala.html", id_sala=sala["id"], senha=sala["senha"], nick=nick, sala_nome=sala_nome)


# Login ADM
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADM_SENHA:
            return redirect(url_for("admin"))
        else:
            flash("Senha incorreta")
            return redirect(url_for("admin_login"))
    return render_template("admin_login.html")


# Painel ADM
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        sala_nome = request.form.get("sala")
        nova_id = request.form.get("id_sala")
        nova_senha = request.form.get("senha_sala")
        if sala_nome in salas:
            salas[sala_nome]["id"] = nova_id
            salas[sala_nome]["senha"] = nova_senha
            flash(f"{sala_nome} atualizado!")
        return redirect(url_for("admin"))
    return render_template("admin.html", salas=salas)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
