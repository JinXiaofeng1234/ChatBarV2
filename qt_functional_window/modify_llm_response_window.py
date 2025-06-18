from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QDialog, QTextEdit, QHBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class TextEditorDialog(QDialog):
    def __init__(self, parent=None, default_text='', width=0, height=0):
        super().__init__(parent)
        self.setWindowTitle('大模型回复修改窗口')
        self.setGeometry(width // 2, height // 2, 400, 300) # 设置对话框位置和大小
        self.setFixedSize(400, 300)

        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e; /* 与主窗口背景色一致 */
                border: 2px solid #555555; /* 与主窗口边框一致 */
                border-radius: 5px; /* 与主窗口边框圆角一致 */
            }
            /* 如果有内部容器，也可以这样设置，例如： */
            QWidget#dialog_content_container {
                background-color: #3c3c3c;
                border: 2px solid #666666;
                border-radius: 8px;
                padding: 10px;
            } 
            QLabel {
                color: #ffffff; /* 确保文本可见 */
            }
            QPushButton {
                background-color: #555555;
                color: #ffffff;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)

        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("幼圆", 14))
        self.text_edit.setObjectName("dialog_content_container")
        self.text_edit.setTextColor(Qt.white)
        if default_text:
            self.text_edit.setText(default_text)
        layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        clear_button = QPushButton('清空')
        clear_button.setFont(QFont("黑体"))
        clear_button.clicked.connect(self.clear_text)
        clear_button.setFixedSize(50, 50)

        close_button = QPushButton('确认')
        close_button.setFont(QFont("黑体"))
        close_button.setFixedSize(50, 50)

        button_layout.addWidget(clear_button)
        button_layout.addWidget(close_button)

        close_button.clicked.connect(self.accept) # 连接到accept()来关闭对话框并返回QDialog.Accepted
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def clear_text(self):
        self.text_edit.clear()

    def get_text(self):
        return self.text_edit.toPlainText()