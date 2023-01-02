import socket
from loguru import logger
import struct
import plotly.express as px
import numpy as np

logger.add('lab_5_ksiit/client_history.log')

# Байты с сервера LabVIEW отправляются задом наперед,
# поэтому разворачиваем их в каждом полученном сообщении
def reverse_bytes(func):
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        return response[::-1]
    return wrapper

def main(ip, port):
    client = socket.socket()
    client.connect((ip, port))
    receive_reversed_bytes = reverse_bytes(client.recv)
    logger.info('Соединение установлено')
    data_bytes = receive_reversed_bytes(4)
    N = int.from_bytes(data_bytes, "little") # кол-во точек сигнала
    # Каждая точка сигнала - число типа double (8 байт)
    signal_msg_len = N*8 # длина следующего сообщения с сигналом
    logger.success('Количество точек получено')
    data_bytes = receive_reversed_bytes(signal_msg_len)
    y_array = [struct.unpack('d', data_bytes[i:i+8])[0] for i in range(0, signal_msg_len, 8)]
    y_array = y_array[::-1] # массив из LabVIEW приходит тоже отзеркаленным
    logger.success('Массив сигнала получен')
    data_bytes = receive_reversed_bytes(8)
    [dt] = struct.unpack('d', data_bytes)
    logger.success('Шаг времени получен')
    data_bytes = receive_reversed_bytes(16)
    logger.success('Время начала сигнала получено')
    client.close()
    logger.info('Соединение разорвано')
    t = np.linspace(0, N*dt, N)
    fig = px.line(x=t, y=y_array, labels={'x':'t', 'y':'received signal'})
    fig.show()
    logger.success('График построен')

if __name__ == '__main__':
    main('127.0.0.1', 5000)



