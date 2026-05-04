from flask import Flask, render_template, request, redirect, url_for, jsonify
import mercadopago
import os

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(ACCESS_TOKEN)

# 🔥 MULTI CLIENTE
usuarios = {
    "eduardo": {
        "salas": {
            "Sala 1": {"id": "123456", "senha": "abcdef", "ocupados": 0, "max": 49},
            "Sala 2": {"id": "654321", "senha": "fedcba", "ocupados": 0, "max": 49}
        },
        "jogadores": []
    }
}

# ---------------- HOME ----------------
@app.route("/<cliente>", methods=["GET", "POST"])
def home(cliente):
    user = usuarios.get(cliente)

    if not user:
        return "Cliente não encontrado"

    if request.method == "POST":
        nick = request.form.get("nick")
        sala_escolhida = request.form.get("sala")

        if not nick:
            return render_template("index.html", erro="Digite seu nick.", salas=user["salas"], cliente=cliente)

        if sala_escolhida not in user["salas"]:
            return render_template("index.html", erro="Sala inválida.", salas=user["salas"], cliente=cliente)

        if user["salas"][sala_escolhida]["ocupados"] >= user["salas"][sala_escolhida]["max"]:
            return render_template("index.html", erro="Sala cheia.", salas=user["salas"], cliente=cliente)

        return redirect(url_for("pago", cliente=cliente, nick=nick, sala=sala_escolhida))

    return render_template("index.html", salas=user["salas"], cliente=cliente)

# ---------------- PAGAMENTO ----------------
@app.route("/<cliente>/pago")
def pago(cliente):
    user = usuarios.get(cliente)

    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")

    if not user or not nick or sala_nome not in user["salas"]:
        return redirect(f"/{cliente}")

    existente = next((j for j in user["jogadores"] if j["nick"] == nick and j["sala"] == sala_nome), None)
    if not existente:
        user["jogadores"].append({
            "nick": nick,
            "sala": sala_nome,
            "pago": False
        })

    payment_data = {
        "transaction_amount": 6.0,
        "description": f"{cliente}-{sala_nome}",
        "payment_method_id": "pix",
        "external_reference": f"{cliente}|{nick}|{sala_nome}",
        "notification_url": "https://sala-ff-2.onrender.com/webhook",
        "payer": {
            "email": f"{nick}@exemplo.com"
        }
    }

    payment = sdk.payment().create(payment_data)

    qr_base64 = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"]
    qr_code = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code"]

    return render_template(
        "pago.html",
        nick=nick,
        qr_code=qr_base64,
        qr_code_text=qr_code,
        sala=sala_nome,
        cliente=cliente
    )

# ---------------- SALA ----------------
@app.route("/<cliente>/sala")
def sala(cliente):
    user = usuarios.get(cliente)

    nick = request.args.get("nick")
    sala_nome = request.args.get("sala")

    jogador = next((j for j in user["jogadores"] if j["nick"] == nick and j["sala"] == sala_nome), None)

    if not jogador or not jogador["pago"]:
        return redirect(f"/{cliente}")

    sala_info = user["salas"][sala_nome]

    return render_template(
        "sala.html",
        id_sala=sala_info["id"],
        senha=sala_info["senha"],
        nick=nick,
        sala=sala_nome
    )

# ---------------- STATUS ----------------
@app.route("/<cliente>/status")
def status(cliente):
    user = usuarios.get(cliente)

    nick = request.args.get("nick")
    sala = request.args.get("sala")

    jogador = next((j for j in user["jogadores"] if j["nick"] == nick and j["sala"] == sala), None)

    return jsonify({"pago": jogador["pago"] if jogador else False})

# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data and data.get("type") == "payment":
        payment_id = data["data"]["id"]

        payment = sdk.payment().get(payment_id)
        status = payment["response"]["status"]

        if status == "approved":
            ref = payment["response"].get("external_reference", "")

            if "|" in ref:
                cliente, nick, sala_nome = ref.split("|")

                user = usuarios.get(cliente)

                jogador = next(
                    (j for j in user["jogadores"] if j["nick"] == nick and j["sala"] == sala_nome),
                    None
                )

                if jogador and not jogador["pago"]:
                    if user["salas"][sala_nome]["ocupados"] < user["salas"][sala_nome]["max"]:
                        jogador["pago"] = True
                        user["salas"][sala_nome]["ocupados"] += 1

    return "OK", 200

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
