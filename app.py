import pytz
import yfinance as yf
import time
import telegram
import requests
from datetime import datetime
print("Ejecutando...")

# ===================================
acciones = ['NVDA', 'AVGO']
UMBRAL = 0.02  # 2%
BUFFER = 0.005  # 0.5%
# ===================================
TELEGRAM_TOKEN = '7859363122:AAHyoZp0CVnJutu8ih5vHrSvSNgZnza6BRs'
TELEGRAM_CHAT_ID = '6814300079'
# ===================================
def enviar_mensaje(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"ERROR (telegram): {e}")

def mercado_abierto():
    zona_est = pytz.timezone("America/New_York")
    ahora = datetime.now(zona_est)
    hora_actual = ahora.time()
    inicio = datetime.strptime("07:30", "%H:%M").time()  # 7:30 AM NY
    fin    = datetime.strptime("17:00", "%H:%M").time()  # 5:00 PM NY
    return inicio <= hora_actual <= fin
# ===================================

# Diccionario para guardar ultimo precio notificado por accion
ultimo_alerta = {}

def obtener_precios(accion):
    try:
        ticker = yf.Ticker(accion)
        hist = ticker.history(period="2d")
        if len(hist) < 2:
            print(f"Historial insuficiente para {accion}")
            return None, None
        cierre_anterior = hist['Close'].iloc[-2]
        info = ticker.info
        if not info or not isinstance(info, dict):
            print(f"{accion}: ERROR - GET_PRICE")
            return None, None
        precio_actual = info.get('regularMarketPrice', None)
        if precio_actual is None:
            print(f"{accion}: ERROR - GET_PRICE")
        return precio_actual, cierre_anterior
    except Exception as e:
        print(f"{accion}: ERROR - GET_PRICE: {e}")
        return None, None

def revisar_variacion():
    for accion in acciones:
        precio_actual, cierre_anterior = obtener_precios(accion)
        if precio_actual is None or cierre_anterior is None:
            print(f"{accion}: ERROR - NO DATA")
            enviar_mensaje(f"{accion}: ERROR - NO DATA")
            continue

        print(f"{accion}: ${precio_actual}")
        variacion = (precio_actual - cierre_anterior) / cierre_anterior

        if accion not in ultimo_alerta:
            if abs(variacion) >= UMBRAL:
                ultimo_alerta[accion] = precio_actual
                print(f"{accion}: REVISAR ({variacion * 100:.2f}%)")
                enviar_mensaje(f"{accion}: REVISAR ({variacion * 100:.2f}%)")
        else:
            precio_ultimo_alerta = ultimo_alerta[accion]
            variacion_nueva = (precio_actual - precio_ultimo_alerta) / precio_ultimo_alerta
            if abs(variacion_nueva) >= BUFFER:
                ultimo_alerta[accion] = precio_actual
                print(f"{accion}: REVISAR ({variacion * 100:.2f}%)")
                enviar_mensaje(f"{accion}: REVISAR ({variacion * 100:.2f}%)")

# ===================================
def main(request: Request):
    if mercado_abierto():
        revisar_variacion()
    return "OK", 200