from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import os

app = Flask(__name__)

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # pegue do Render
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Salas e informações iniciais (você pode editar o ID e senha no ADM)
salas = {
    "Sala 1": {"id": "123456", "senha": "abcdef", "jogadores": []},
    "Sala 2": {"id": "654321", "senha": "fedcba", "jogadores": []}
}

# Senha do painel ADM
ADM_SENHA = "Duduzin321@"

# Página inicial
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala_nome = request.form.get("sala")
        if not nick or not sala_nome:
            return render_template("index.html", salas=salas, erro="Preencha nick e escolha uma sala.")
        return redirect(url_for("pago", nick=nick, sala=sala_nome))
    return render_template("index.html", salas=salas)

# Página de pagamento
@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")
    if not nick or not sala_nome or sala_nome not in salas:
        return redirect(url_for("home"))

    # Criar pagamento Mercado Pago
    payment_data = {
        "transaction_amount": 6.0,
        "description": f"Recarga {sala_nome}",
        "payment_method_id": "pix",
        "payer": {"email": f"{nick}@exemplo.com"}
    }
    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    copia_colar = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")

    # Adiciona jogador à sala
    if nick not in salas[sala_nome]["jogadores"]:
        salas[sala_nome]["jogadores"].append({"nick": nick, "pago": False})

    return render_template("pago.html", nick=nick, sala_nome=sala_nome, qr_code=qr_code, copia_colar=copia_colar)

# Página da sala
@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")
    if not nick or not sala_nome or sala_nome not in salas:
        return redirect(url_for("home"))
    # Verifica se jogador pagou (simulado aqui como True)
    return render_template("sala.html", id_sala=salas[sala_nome]["id"], senha=salas[sala_nome]["senha"], nick=nick)

# Painel ADM
@app.route("/adm", methods=["GET", "POST"])
def adm():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha != ADM_SENHA:
            erro = "Senha incorreta!"
        else:
            return redirect(url_for("adm_painel"))
    return render_template("adm_login.html", erro=erro)

@app.route("/adm/painel")
def adm_painel():
    return render_template("admin.html", salas=salas)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
