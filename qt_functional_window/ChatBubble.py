import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class ChatBubble(QWidget):
    def __init__(self, message, is_user=True, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.setFixedHeight(60)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取文本大小
        font_metrics = QFontMetrics(self.font())
        text_rect = font_metrics.boundingRect(self.message)

        # 计算气泡大小和位置
        bubble_width = min(max(text_rect.width() + 40, 80), 300)
        bubble_height = 40

        if self.is_user:
            # 用户消息：右侧，蓝色
            bubble_rect = QRect(self.width() - bubble_width - 10, 10, bubble_width, bubble_height)
            bubble_color = QColor(0, 123, 255)
            text_color = Qt.white
        else:
            # 电脑消息：左侧，灰色
            bubble_rect = QRect(10, 10, bubble_width, bubble_height)
            bubble_color = QColor(233, 236, 239)
            text_color = Qt.black

        # 绘制气泡
        painter.setBrush(QBrush(bubble_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bubble_rect, 15, 15)

        # 绘制文本
        painter.setPen(text_color)
        painter.drawText(bubble_rect, Qt.AlignCenter, self.message)


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('气泡式对话窗口 Demo')
        self.setGeometry(300, 300, 400, 600)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # 创建聊天区域
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        # 修正：使用正确的ScrollBarPolicy枚举值
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 聊天内容容器
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(5)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)

        # 添加弹性空间，让消息从底部开始
        self.chat_layout.addStretch()

        self.chat_area.setWidget(self.chat_container)
        layout.addWidget(self.chat_area)

        # 创建输入区域
        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setFixedHeight(40)
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("发送")
        self.send_button.setFixedSize(60, 40)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QScrollArea {
                border: none;
                background-color: white;
                border-radius: 10px;
            }
            QLineEdit {
                border: 2px solid #dee2e6;
                border-radius: 20px;
                padding: 0 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)

        # 添加欢迎消息
        self.add_message("Hello! 我是智能助手，请随时向我发送消息！", is_user=False)

    def add_message(self, message, is_user=True):
        # 移除弹性空间
        self.chat_layout.removeItem(self.chat_layout.itemAt(self.chat_layout.count() - 1))

        # 添加新消息气泡
        bubble = ChatBubble(message, is_user)
        self.chat_layout.addWidget(bubble)

        # 重新添加弹性空间
        self.chat_layout.addStretch()

        # 滚动到底部
        QTimer.singleShot(50, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            # 添加用户消息
            self.add_message(message, is_user=True)
            self.message_input.clear()

            # 模拟处理延迟，然后回复hello
            QTimer.singleShot(500, self.send_reply)

    def send_reply(self):
        # 电脑自动回复hello
        self.add_message("hello", is_user=False)


class ChatApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.setApplicationName("气泡对话Demo")

        # 设置应用图标（可选）
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))


def main():
    app = ChatApp(sys.argv)

    # 创建并显示主窗口
    window = ChatWindow()
    window.show()

    # 启动事件循环
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
