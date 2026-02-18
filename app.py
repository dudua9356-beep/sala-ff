from flask import Flask, render_template, request, redirect, url_for, session, flash
import mercadopago
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")  # Para sessões

# Mercado Pago
ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Senha do admin
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

# Salas disponíveis (exemplo inicial)
MAX_JOGADORES = 49
salas = {
    "Sala FF 🔥": {"id": "123456", "senha": "abcdef", "valor": 6.0}
}

# Lista de jogadores que já pagaram por sala
pagamentos = {nome_sala: [] for nome_sala in salas.keys()}

# =========================
# Fluxo público
# =========================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nick = request.form.get("nick")
        sala = request.form.get("sala")
        if not nick:
            return render_template("index.html", salas=salas, erro="Digite seu nick do Free Fire.")
        if sala not in salas:
            return render_template("index.html", salas=salas, erro="Sala inválida.")
        if len(pagamentos[sala]) >= MAX_JOGADORES:
            return render_template("index.html", salas=salas, erro="Sala lotada! Tente outra.")
        return redirect(url_for("pago", nick=nick, sala=sala))
    return render_template("index.html", salas=salas)

@app.route("/pago")
def pago():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala or sala not in salas:
        return redirect(url_for("home"))

    if len(pagamentos[sala]) >= MAX_JOGADORES:
        return render_template("index.html", salas=salas, erro="Sala lotada! Tente outra.")

    valor = salas[sala]["valor"]

    # Criar pagamento no Mercado Pago
    payment_data = {
        "transaction_amount": valor,
        "description": f"Recarga {sala}",
        "payment_method_id": "pix",
        "payer": {
            "email": f"{nick}@exemplo.com"
        }
    }

    payment = sdk.payment().create(payment_data)
    qr_code = payment["response"].get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")

    # Salva jogador na lista de pagamentos (temporário)
    if nick not in pagamentos[sala]:
        pagamentos[sala].append(nick)

    return render_template("pago.html", nick=nick, qr_code=qr_code, sala=sala)

@app.route("/sala")
def sala():
    nick = request.args.get("nick")
    sala = request.args.get("sala")
    if not nick or not sala or nick not in pagamentos.get(sala, []):
        return redirect(url_for("home"))

    id_sala = salas[sala]["id"]
    senha_sala = salas[sala]["senha"]
    return render_template("sala.html", nick=nick, id_sala=id_sala, senha_sala=senha_sala, sala=sala)

# =========================
# Painel Administrativo
# =========================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin_logged" not in session:
        return redirect(url_for("admin_login"))
    return render_template("admin.html", salas=salas, pagamentos=pagamentos)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADMIN_PASS:
            session["admin_logged"] = True
            return redirect(url_for("admin"))
        flash("Senha incorreta.")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/adicionar_sala", methods=["POST"])
def adicionar_sala():
    if "admin_logged" not in session:
        return redirect(url_for("admin_login"))
    nome = request.form.get("nome")
    id_sala = request.form.get("id_sala")
    senha_sala = request.form.get("senha_sala")
    valor = float(request.form.get("valor", 6.0))
    if nome and id_sala and senha_sala:
        salas[nome] = {"id": id_sala, "senha": senha_sala, "valor": valor}
        pagamentos[nome] = []
    return redirect(url_for("admin"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
