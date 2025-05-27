#from PySide6.QtGui import QGuiApplication
#from PySide6.QtQml import QQmlApplicationEngine
#from PySide6.QtCore import QUrl

# dashboard.py

import sys
import os

from PyQt5.QtGui    import QGuiApplication
from PyQt5.QtQml    import QQmlApplicationEngine
from PyQt5.QtCore   import QUrl, QObject, pyqtSignal, pyqtSlot, QTimer

class UIBackend(QObject):
    # 定义一个 string 类型的信号，用来从 Python 端向 QML 发指令
    commandIssued = pyqtSignal(str)

    @pyqtSlot(str)
    def requestAction(self, cmd):
        # QML 可以调用这个方法来向后端发请求
        print(f"🔷 前端请求动作：{cmd}")

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

    # 4. 简单测试：1 秒后发出一个 “PlayMusic” 指令给 QML
    QTimer.singleShot(3000, lambda: ui_backend.commandIssued.emit("PlayMusic"))

    # 5. 进入 Qt 事件循环
    sys.exit(app.exec_())
