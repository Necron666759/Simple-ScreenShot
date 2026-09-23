"""Простой IPC на локальном сокете, чтобы приложение работало одним
экземпляром в трее (аналогично Flameshot), а команды вроде
`simple-screenshot --capture` (например, назначенные как хоткей в
настройках окружения на Wayland) отправлялись уже запущенному процессу."""
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "simple-screenshot-ipc"


def send_command(command, timeout=500):
    """Пытается передать команду уже запущенному экземпляру.
    Возвращает True, если экземпляр был найден и команда отправлена."""
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if not socket.waitForConnected(timeout):
        return False
    socket.write(command.encode("utf-8"))
    socket.flush()
    socket.waitForBytesWritten(timeout)
    socket.disconnectFromServer()
    return True


def start_server(on_command):
    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer()
    server.listen(SERVER_NAME)

    def handle_new_connection():
        socket = server.nextPendingConnection()
        if socket is None:
            return

        def on_ready_read():
            data = bytes(socket.readAll()).decode("utf-8", errors="ignore")
            if data:
                on_command(data)
            socket.disconnectFromServer()

        socket.readyRead.connect(on_ready_read)

    server.newConnection.connect(handle_new_connection)
    return server
