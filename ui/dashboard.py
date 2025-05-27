#from PySide6.QtGui import QGuiApplication
#from PySide6.QtQml import QQmlApplicationEngine
#from PySide6.QtCore import QUrl

# dashboard.py

import requests
import sys
import os

from PyQt5.QtGui    import QGuiApplication
from PyQt5.QtQml    import QQmlApplicationEngine
from PyQt5.QtCore   import QUrl, QObject, pyqtSignal, pyqtSlot, QTimer

class UIBackend(QObject):
    # 定义一个 string 类型的信号，用来从 Python 端向 QML 发指令
    commandIssued = pyqtSignal(str)
    # 天气
    weatherUpdated = pyqtSignal(str)

    @pyqtSlot(str)
    def requestAction(self, cmd):
        # QML 可以调用这个方法来向后端发请求
        print(f"🔷 前端请求动作：{cmd}")


def fetch_weather(city="Tianjin"):
    #api_key = "e8527d822a260a90258bbbcf110506e8"
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Tianjin&appid=e8527d822a260a90258bbbcf110506e8&units=metric&lang=zh_cn"

    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if res.status_code == 200:
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"{round(temp)}°C {desc}"
        else:
            print("❌ 天气 API 响应失败：", data)
            return "天气加载失败"
    except Exception as e:
        print("❌ 请求天气失败：", e)
        return "天气异常"


if __name__ == "__main__":
    # 1. 创建 Qt 应用与 QML 引擎
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # 2. 实例化桥接对象并注入到 QML 上下文
    ui_backend = UIBackend()
    engine.rootContext().setContextProperty("UIBackend", ui_backend)

    # 3. 加载 Main.qml
    base_dir = os.path.dirname(__file__)
    qml_file = os.path.join(base_dir, "Main.qml")
    print(f"🔍 正在加载 QML：{qml_file}")
    engine.load(QUrl.fromLocalFile(qml_file))
    if not engine.rootObjects():
        print("❌ QML 加载失败，请检查路径或语法错误！")
        sys.exit(-1)

    weather_text = fetch_weather("Tianjin")
    QTimer.singleShot(1000, lambda: ui_backend.weatherUpdated.emit(weather_text))

    QTimer.singleShot(3000, lambda: ui_backend.weatherUpdated.emit("30°C 多云"))

    QTimer.singleShot(5000, lambda: ui_backend.weatherUpdated.emit("25°C 下雨"))

    # 4. 简单测试：1 秒后发出一个 “PlayMusic” 指令给 QML
    QTimer.singleShot(3000, lambda: ui_backend.commandIssued.emit("PlayMusic"))

    QTimer.singleShot(5000, lambda: ui_backend.commandIssued.emit("distract"))

    QTimer.singleShot(7000, lambda: ui_backend.commandIssued.emit("NoticeRoad"))

    # 5. 进入 Qt 事件循环
    sys.exit(app.exec_())
