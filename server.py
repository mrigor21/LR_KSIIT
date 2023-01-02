import socket
from loguru import logger
import numpy as np
import time
import struct
import plotly.express as px

logger.add('server_history.log')

# Сервер на LabVIEW разворачивает данные при отправке,
# и клиент LabVIEW ждет также развернутые байты
# Этот декоратор будет разворачивать байты сообщения перед отправкой,
# чтобы клиент LabVIEW воспринял их правильно
def reverse_bytes(func):
    def wrapper(*args, **kwargs):
        args = list(args)
        args[0] = args[0][::-1]
        response = func(*args, **kwargs)
        return response
    return wrapper

def ask_for_signal_params():
    while True:
        try:
            freq = float(input("Введите частоту отправляемого сигнала: "))
            amp = float(input("Введите амплитуду отправляемого сигнала: "))
            break
        except Exception:
            logger.error('Амплитуда или частота введены неверно, повторите попытку')
    return amp, freq

def main(ip, port):
    server = socket.socket()
    server.bind((ip, port))
    server.listen(1)
    logger.success('Сервер запущен')
    N, D = 200, 20000 # Кол-во точек, частота дискретизации
    dt = 1/D
    stop = False
    while not stop:
        amp, freq = ask_for_signal_params()
        # Условный сигнал к остановке сервера – отрицательная частота или амплитуда
        stop = True if amp < 0 or freq < 0 else False
        if stop:
            logger.success('Сервер остановлен')
            continue # пропуск тела цила, если подан сигнал остановки сервера
        t = np.linspace(0, dt * N, N)
        y_array = amp*np.sin(2*np.pi*freq*t)
        fig = px.line(x=t, y=y_array, labels={'x':'t', 'y':'sent signal'})
        fig.show()
        logger.success('График построен')
        logger.info('Ожидание соединения...')
        client_socket, adress = server.accept()
        send_reversed_bytes = reverse_bytes(client_socket.send)
        N_bytes = struct.pack("i", N)
        send_reversed_bytes(N_bytes)
        logger.success('Количество точек отправлено')
        y_array = y_array[::-1] # массив тоже разворачиваем, повторяем LabVIEW
        y_array_bytes = struct.pack('d'*len(y_array),*y_array)
        send_reversed_bytes(y_array_bytes)
        logger.success('Массив сигнала отправлен')
        dt_bytes = struct.pack('d', dt)
        send_reversed_bytes(dt_bytes)
        logger.success('Шаг времени отправлен')
        ts_bytes = struct.pack('d'*16, *[0]*16)
        logger.success('Время начала сигнала отправлено')
        send_reversed_bytes(ts_bytes)
        client_socket.close()
        time.sleep(0.2)
    
if __name__ == '__main__':
    main('127.0.0.1', 5000)


    