import websocket
import json
import time

def on_message(ws, message):
    order_book = json.loads(message)
    print(len(order_book['a']))
    time.sleep(3)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("Connection closed")

def on_open(ws):
    symbol = 'ethusdt'
    message = {
        "method": "SUBSCRIBE",
        "params": [
            f"{symbol}@depth@1000ms"
        ],
        "id": 1
    }
    ws.send(json.dumps(message))

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws",
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
