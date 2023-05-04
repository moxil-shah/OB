import threading
import time
import websocket
import queue

buffer = queue.Queue()

def read_websocket():
    def on_message(ws, message):
        buffer.put(message)

    def on_error(ws, error):
        print(error)

    def on_close(ws):
        print("Connection closed")

    def on_open(ws):
        print("Connection opened")

    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    ws.on_open = on_open

    ws.run_forever()

def do_other_stuff():
    while True:
        local_array = []
        try:
            message = buffer.get()
            while message is not None:
                local_array.append(message)
                message = buffer.get()
        except queue.Empty:
            pass
        print(local_array)


if __name__ == "__main__":
    websocket_thread = threading.Thread(target=read_websocket)
    other_thread = threading.Thread(target=do_other_stuff)

    websocket_thread.start()
    other_thread.start()

    websocket_thread.join()
    other_thread.join()
