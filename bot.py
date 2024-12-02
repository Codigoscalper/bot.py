from flask import Flask, request
import requests
import os

app = Flask(__name__)  # Corrección aquí: __name__ es el parámetro adecuado

# Token del bot de Telegram
BOT_TOKEN = "8093427771:AAHdXGLe1VBpXWdyCwBEcSIW6X5UEptVmS0"  # Reemplaza con tu token

# IDs de grupo y temas
GROUP_CHAT_ID = "-1002315274627"  # Reemplaza con el ID de tu grupo
TOPICS = {
    "BTC": 2,    # Tema para Bitcoin Señales
    "ETH": 9,    # Tema para Ethereum Señales
    "ADA": 55,   # Tema para ADA/USDT Cardano Señales
    "XRP": 50,   # Tema para XRP/USDT Ledger Señales
    "BNB": 43    # Tema para BNB Señales
}

# Variable global para almacenar precios de entrada
precios_entrada = {"BTC": None, "ETH": None, "ADA": None, "XRP": None, "BNB": None}
APALANCAMIENTO = 3  # Apalancamiento fijo

@app.route('/webhook', methods=['POST'])
def webhook():
    global precios_entrada

    # Recibe el JSON enviado desde TradingView
    data = request.json

    # Extrae información de la alerta de TradingView
    ticker = data.get('ticker', 'No especificado')  # Ticker del activo
    action = data.get('order_action', 'No especificado').lower()  # Tipo de acción (buy/sell/close)
    order_price = data.get('order_price', None)  # Precio de la orden

    # Determinar el tema basado en el ticker
    if "BTC" in ticker:
        asset = "BTC"
        topic_id = TOPICS.get("BTC")
    elif "ETH" in ticker:
        asset = "ETH"
        topic_id = TOPICS.get("ETH")
    elif "ADA" in ticker:
        asset = "ADA"
        topic_id = TOPICS.get("ADA")
    elif "XRP" in ticker:
        asset = "XRP"
        topic_id = TOPICS.get("XRP")
    elif "BNB" in ticker:
        asset = "BNB"
        topic_id = TOPICS.get("BNB")
    else:
        # Si el activo no es reconocido, no hacemos nada
        return "Activo no reconocido", 400

    # Manejo de acciones
    if action == "buy":
        # Almacena el precio de entrada
        precios_entrada[asset] = float(order_price) if order_price else None
        mensaje_telegram = (
            f"🟢 **ABRIR POSICIÓN {asset}** 🟢\n\n"
            f"📈 Activo: {asset}/USDT\n"
            f"💰 Precio: {order_price}\n"
            f"💼 Acción: **COMPRA**\n\n"
            f"🔒 **Apalancamiento:** {APALANCAMIENTO}x"
        )
    elif action in ["sell", "close"]:
        if precios_entrada[asset] and order_price:
            precio_salida = float(order_price)
            # Calcula la ganancia o pérdida porcentual
            profit_percentage = ((precio_salida - precios_entrada[asset]) / precios_entrada[asset]) * 100
            profit_percentage_leveraged = profit_percentage * APALANCAMIENTO  # Ajuste por apalancamiento
            if profit_percentage_leveraged > 0:
                profit_text = f"🟢 **Ganancia:** +{profit_percentage_leveraged:.2f}%"
            else:
                profit_text = f"🔴 **Pérdida:** {profit_percentage_leveraged:.2f}%"
            mensaje_telegram = (
                f"🔴 **CERRAR POSICIÓN {asset}** 🔴\n\n"
                f"📈 Activo: {asset}/USDT\n"
                f"💰 Precio: {order_price}\n"
                f"💼 Acción: **CERRAR**\n\n"
                f"{profit_text}"
            )
            # Reinicia el precio de entrada después de cerrar
            precios_entrada[asset] = None
        else:
            mensaje_telegram = (
                f"🔴 **CERRAR POSICIÓN {asset}** 🔴\n\n"
                f"📈 Activo: {asset}/USDT\n"
                f"💰 Precio: {order_price}\n"
                f"💼 Acción: **CERRAR**\n\n"
                f"🔒 No se pudo calcular la ganancia o pérdida."
            )
    else:
        mensaje_telegram = (
            f"⚡ **SEÑAL DE {asset}** ⚡\n\n"
            f"📈 Activo: {asset}/USDT\n"
            f"💰 Precio: {order_price}\n"
            f"💼 Acción: {action.capitalize()}"
        )

    # Envía el mensaje al tema correspondiente
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': GROUP_CHAT_ID,
        'message_thread_id': topic_id,  # Especifica el tema
        'text': mensaje_telegram,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, json=payload)

    # Imprime la respuesta para depurar si hay errores
    print(response.json())

    return "OK", 200  # Respuesta para TradingView


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
