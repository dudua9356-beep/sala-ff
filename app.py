from flask import Flask, render_template, request, redirect, url_for
import mercadopago
import json
import os
import uuid

app = Flask(__name__)

# Configurar seu token Mercado Pago aqui
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # ou coloque sua chave aqui diretamente
mp = mercadopago.SDK(MP_ACCESS_TOKEN)

# Arquivo simples para armazenar salas e pagamentos
DATABASE = "data.json"

# Inicializa DB se não existir
if not os.path.exists(DATABASE):
    with open(DATABASE, "w") as f:
        json.dump({"salas": {}, "compradores": {}}, f)

def load_db():
    with open(DATABASE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DATABASE, "w") as f:
        json.dump(data, f, indent=4)

# Página inicial / admin
@app.route("/admin", methods=["GET", "POST"])
def admin():
    data = load_db()
    if request.method == "POST":
        # Criar nova sala
        sala_id = request.form["sala_id"]
        senha = request.form["senha"]
        link = str(uuid.uuid4())
        data["salas"][link] = {
            "sala_id": sala_id,
            "senha": senha,
            "jogadores": []
        }
        save_db(data)
        return render_template("admin.html", salas=data["salas"], message=f"Sala criada! Link: {request.url_root}sala/{link}")
    return render_template("admin.html", salas=data["salas"])

# Página de cada sala
@app.route("/sala/<link>", methods=["GET", "POST"])
def sala(link):
    data = load_db()
    sala = data["salas"].get(link)
    if not sala:
        return "Sala inválida ou não existe."

    if request.method == "POST":
        nick = request.form["nick"]
        # Cria pagamento Mercado Pago
        payment_data = {
            "transaction_amount": 6,
            "description": f"Entrada Sala FF - {nick}",
            "payment_method_id": "pix",
            "payer": {"email": f"{nick}@example.com"}  # só um dummy
        }
        payment = mp.payment().create(payment_data)
        payment_id = payment["response"]["id"]

        # Salva jogador aguardando pagamento
        sala["jogadores"].append({"nick": nick, "payment_id": payment_id, "status": "pendente"})
        data["salas"][link] = sala
        save_db(data)

        # Link de pagamento PIX
        pix_link = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        return render_template("pago.html", qr=pix_link, nick=nick, sala_id=sala["sala_id"], senha=sala["senha"])

    return render_template("sala.html", link=link)

# Webhook Mercado Pago
@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.json
    payment_id = event["data"]["id"]
    data = load_db()
    for sala in data["salas"].values():
        for jogador in sala["jogadores"]:
            if jogador["payment_id"] == payment_id:
                jogador["status"] = "pago"
                save_db(data)
                break
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
