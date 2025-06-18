import sys
import json
from PyQt5.QtWidgets import (QApplication, QDialog, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QComboBox, QPushButton,
                             QListWidget, QListWidgetItem, QMessageBox, QCheckBox,
                             QFileDialog, QLabel)
from PyQt5.QtCore import Qt


class ChatManager(QDialog):
    def __init__(self, conversation_history=None, obj=None):
        super().__init__()
        self.obj = obj
        self.setWindowTitle('聊天会话管理窗口')
        self.setGeometry(100, 100, 1000, 700)

        # 主窗口部件
        layout = QHBoxLayout(self)

        # 左侧消息列表区域
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        # 文件操作按钮
        file_controls = QHBoxLayout()

        self.load_file_btn = QPushButton('Load JSON File')
        self.load_file_btn.clicked.connect(self.load_json_file)
        file_controls.addWidget(self.load_file_btn)

        self.save_file_btn = QPushButton('Save JSON File')
        self.save_file_btn.clicked.connect(self.save_json_file)
        file_controls.addWidget(self.save_file_btn)

        left_layout.addLayout(file_controls)

        # 文件路径显示
        self.file_path_label = QLabel('No file loaded')
        self.file_path_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        left_layout.addWidget(self.file_path_label)

        # 批量操作控制按钮
        select_controls = QHBoxLayout()

        self.toggle_select_btn = QPushButton('Enable Selection')
        self.toggle_select_btn.setCheckable(True)
        self.toggle_select_btn.clicked.connect(self.toggle_selection_mode)
        select_controls.addWidget(self.toggle_select_btn)

        self.select_all_cb = QCheckBox('Select All')
        self.select_all_cb.setVisible(False)
        self.select_all_cb.stateChanged.connect(self.select_all_changed)
        select_controls.addWidget(self.select_all_cb)

        self.delete_selected_btn = QPushButton('Delete Selected')
        self.delete_selected_btn.setVisible(False)
        self.delete_selected_btn.clicked.connect(self.delete_selected)
        select_controls.addWidget(self.delete_selected_btn)

        left_layout.addLayout(select_controls)

        # 消息列表
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_message)
        left_layout.addWidget(self.chat_list)

        # 列表操作按钮
        list_controls = QHBoxLayout()

        self.move_up_btn = QPushButton('↑ Move Up')
        self.move_up_btn.clicked.connect(self.move_message_up)
        list_controls.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton('↓ Move Down')
        self.move_down_btn.clicked.connect(self.move_message_down)
        list_controls.addWidget(self.move_down_btn)

        left_layout.addLayout(list_controls)

        # 右侧编辑区域
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        # 编辑区域标题
        edit_label = QLabel('Message Editor')
        edit_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        right_layout.addWidget(edit_label)

        # 角色选择
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel('Role:'))
        self.role_selector = QComboBox()
        self.role_selector.addItems(['user', 'assistant', 'system'])
        role_layout.addWidget(self.role_selector)
        role_layout.addStretch()
        right_layout.addLayout(role_layout)

        # 消息编辑框
        right_layout.addWidget(QLabel('Content:'))
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Enter message content here...")
        right_layout.addWidget(self.message_edit)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.add_button = QPushButton('Add Message')
        self.add_button.clicked.connect(self.add_message)
        self.add_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(self.add_button)

        self.update_button = QPushButton('Update Message')
        self.update_button.clicked.connect(self.update_message)
        self.update_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        button_layout.addWidget(self.update_button)

        self.delete_button = QPushButton('Delete Message')
        self.delete_button.clicked.connect(self.delete_message)
        self.delete_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        button_layout.addWidget(self.delete_button)

        # 在按钮区域添加插入按钮
        self.insert_button = QPushButton('Insert Message')
        self.insert_button.clicked.connect(self.insert_message)
        self.insert_button.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        button_layout.addWidget(self.insert_button)  # 在现有的按钮布局中添加

        self.clear_button = QPushButton('Clear Editor')
        self.clear_button.clicked.connect(self.clear_editor)
        button_layout.addWidget(self.clear_button)

        self.confoirm_btn = QPushButton('confirm')
        self.confoirm_btn.clicked.connect(self.confirm_changes)
        button_layout.addWidget(self.confoirm_btn)

        right_layout.addLayout(button_layout)

        # 消息统计
        self.stats_label = QLabel('Messages: 0')
        self.stats_label.setStyleSheet("padding: 5px; background-color: #e8e8e8; border: 1px solid #ccc;")
        right_layout.addWidget(self.stats_label)

        # 添加左右布局到主布局
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        # 设置布局比例
        layout.setStretch(0, 5)
        layout.setStretch(1, 5)

        self.current_item = None
        self.selection_mode = False
        self.current_file_path = None

        if conversation_history:
            # print(obj.conversation_history)
            if isinstance(conversation_history, list):
                self.load_chat_history(conversation_history)
                QMessageBox.information(self, 'Success', f'Loaded messages successfully!')
            else:
                QMessageBox.warning(self, 'Error', 'Invalid JSON format. Expected a list of messages.')

    def create_list_item_widget(self, role, content):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        checkbox = QCheckBox()
        checkbox.setVisible(self.selection_mode)
        layout.addWidget(checkbox)

        # 角色标签
        role_label = QLabel(f"[{role}]")
        role_label.setFixedWidth(80)
        if role == "system":
            role_label.setStyleSheet("color: #FF6B35; font-weight: bold;")
        elif role == "user":
            role_label.setStyleSheet("color: #004E89; font-weight: bold;")
        else:  # assistant
            role_label.setStyleSheet("color: #009639; font-weight: bold;")
        layout.addWidget(role_label)

        # 内容预览
        content_preview = content.replace('\n', ' ')[:50]
        if len(content) > 50:
            content_preview += "..."

        text_label = QLabel(content_preview)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)

        widget.setLayout(layout)
        return widget, checkbox

    def add_message_from_data(self, role, content):
        """从数据添加消息（不清空编辑框）"""
        item = QListWidgetItem()
        widget, checkbox = self.create_list_item_widget(role, content)
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.UserRole, {
            'role': role,
            'content': content,
            'checkbox': checkbox
        })

        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, widget)
        self.update_stats()

    def add_message(self):
        """增加新消息"""
        role = self.role_selector.currentText()
        content = self.message_edit.toPlainText()

        if not content.strip():
            QMessageBox.warning(self, 'Warning', 'Message cannot be empty!')
            return

        self.add_message_from_data(role, content)
        self.message_edit.clear()

    def load_message(self, item):
        """查询/载入消息到编辑器"""
        # 如果在选择模式下，点击项目时切换复选框状态
        if self.selection_mode:
            data = item.data(Qt.UserRole)
            checkbox = data['checkbox']
            checkbox.setChecked(not checkbox.isChecked())
            return

        self.current_item = item
        data = item.data(Qt.UserRole)
        self.role_selector.setCurrentText(data['role'])
        self.message_edit.setText(data['content'])

    def update_message(self):
        """修改当前选中的消息"""
        if not self.current_item:
            QMessageBox.warning(self, 'Warning', 'Please select a message to update!')
            return

        role = self.role_selector.currentText()
        content = self.message_edit.toPlainText()

        if not content.strip():
            QMessageBox.warning(self, 'Warning', 'Message cannot be empty!')
            return

        widget, checkbox = self.create_list_item_widget(role, content)
        self.current_item.setSizeHint(widget.sizeHint())
        self.current_item.setData(Qt.UserRole, {
            'role': role,
            'content': content,
            'checkbox': checkbox
        })
        self.chat_list.setItemWidget(self.current_item, widget)

    def delete_message(self):
        """删除当前选中的消息"""
        if not self.current_item:
            QMessageBox.warning(self, 'Warning', 'Please select a message to delete!')
            return

        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     'Delete this message?',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            row = self.chat_list.row(self.current_item)
            self.chat_list.takeItem(row)
            self.current_item = None
            self.message_edit.clear()
            self.update_stats()

    def insert_message(self):
        """在当前选中的消息前插入新消息"""
        current_row = self.chat_list.currentRow()
        if current_row == -1:
            # 如果没有选中任何消息，则在末尾添加
            self.add_message()
            return

        role = self.role_selector.currentText()
        content = self.message_edit.toPlainText()

        if not content.strip():
            QMessageBox.warning(self, 'Warning', 'Message cannot be empty!')
            return

        # 创建新项并插入
        item = QListWidgetItem()
        widget, checkbox = self.create_list_item_widget(role, content)
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.UserRole, {
            'role': role,
            'content': content,
            'checkbox': checkbox
        })

        self.chat_list.insertItem(current_row, item)
        self.chat_list.setItemWidget(item, widget)

        # 选中新插入的项
        self.chat_list.setCurrentRow(current_row)
        self.current_item = item
        self.update_stats()

    def clear_editor(self):
        """清空编辑器"""
        self.message_edit.clear()
        self.current_item = None
        self.role_selector.setCurrentIndex(0)

    def confirm_changes(self):
        self.obj.conversation_history = self.get_chat_history()

    def move_message_up(self):
        """向上移动消息"""
        current_row = self.chat_list.currentRow()
        if current_row > 0:
            item = self.chat_list.takeItem(current_row)
            self.chat_list.insertItem(current_row - 1, item)

            # 重新创建widget
            data = item.data(Qt.UserRole)
            widget, checkbox = self.create_list_item_widget(data['role'], data['content'])
            data['checkbox'] = checkbox
            item.setData(Qt.UserRole, data)
            self.chat_list.setItemWidget(item, widget)

            self.chat_list.setCurrentRow(current_row - 1)

    def move_message_down(self):
        """向下移动消息"""
        current_row = self.chat_list.currentRow()
        if current_row < self.chat_list.count() - 1:
            item = self.chat_list.takeItem(current_row)
            self.chat_list.insertItem(current_row + 1, item)

            # 重新创建widget
            data = item.data(Qt.UserRole)
            widget, checkbox = self.create_list_item_widget(data['role'], data['content'])
            data['checkbox'] = checkbox
            item.setData(Qt.UserRole, data)
            self.chat_list.setItemWidget(item, widget)

            self.chat_list.setCurrentRow(current_row + 1)

    def toggle_selection_mode(self, checked):
        """切换批量选择模式"""
        self.selection_mode = checked
        self.select_all_cb.setVisible(checked)
        self.delete_selected_btn.setVisible(checked)

        # 更新所有项目的复选框可见性
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            data = item.data(Qt.UserRole)
            checkbox = data['checkbox']
            checkbox.setVisible(checked)
            if not checked:
                checkbox.setChecked(False)

        if not checked:
            self.select_all_cb.setChecked(False)

        self.toggle_select_btn.setText('Disable Selection' if checked else 'Enable Selection')

    def select_all_changed(self, state):
        """全选/取消全选"""
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            data = item.data(Qt.UserRole)
            checkbox = data['checkbox']
            checkbox.setChecked(state == Qt.Checked)

    def delete_selected(self):
        """批量删除选中的消息"""
        items_to_remove = []
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            data = item.data(Qt.UserRole)
            if data['checkbox'].isChecked():
                items_to_remove.append(item)

        if not items_to_remove:
            QMessageBox.warning(self, 'Warning', 'No messages selected!')
            return

        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     f'Delete {len(items_to_remove)} selected messages?',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            for item in items_to_remove:
                row = self.chat_list.row(item)
                self.chat_list.takeItem(row)

            self.current_item = None
            self.message_edit.clear()
            self.update_stats()

    def load_json_file(self):
        """载入JSON聊天记录文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Open JSON Chat File', '', 'JSON files (*.json);;All files (*.*)')

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)["memory"]

                if isinstance(chat_data, list):
                    self.load_chat_history(chat_data)
                    self.current_file_path = file_path
                    self.file_path_label.setText(f"Loaded: {file_path}")
                    QMessageBox.information(self, 'Success', f'Loaded {len(chat_data)} messages successfully!')
                else:
                    QMessageBox.warning(self, 'Error', 'Invalid JSON format. Expected a list of messages.')

            except json.JSONDecodeError as e:
                QMessageBox.critical(self, 'Error', f'Failed to parse JSON file:\n{str(e)}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to load file:\n{str(e)}')

    def save_json_file(self):
        """保存聊天记录到JSON文件"""
        if self.chat_list.count() == 0:
            QMessageBox.warning(self, 'Warning', 'No messages to save!')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Save JSON Chat File', '', 'JSON files (*.json);;All files (*.*)')

        if file_path:
            try:
                chat_data = self.get_chat_history()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(chat_data, f, ensure_ascii=False, indent=4)

                self.current_file_path = file_path
                self.file_path_label.setText(f"Saved: {file_path}")
                QMessageBox.information(self, 'Success', f'Saved {len(chat_data)} messages successfully!')

            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save file:\n{str(e)}')

    def load_chat_history(self, chat_data):
        """从聊天数据列表载入历史记录"""
        # 清空现有数据
        self.chat_list.clear()
        self.current_item = None
        self.message_edit.clear()

        # 载入数据
        for message in chat_data:
            if isinstance(message, dict) and 'role' in message and 'content' in message:
                self.add_message_from_data(message['role'], message['content'])
            else:
                print(f"Invalid message format: {message}")

    def update_stats(self):
        """更新消息统计"""
        count = self.chat_list.count()
        user_count = sum(1 for i in range(count)
                         if self.chat_list.item(i).data(Qt.UserRole)['role'] == 'user')
        assistant_count = sum(1 for i in range(count)
                              if self.chat_list.item(i).data(Qt.UserRole)['role'] == 'assistant')
        system_count = sum(1 for i in range(count)
                           if self.chat_list.item(i).data(Qt.UserRole)['role'] == 'system')

        self.stats_label.setText(
            f"Total: {count} | User: {user_count} | Assistant: {assistant_count} | System: {system_count}")

    def get_chat_history(self):
        """获取聊天记录（JSON格式）"""
        chat_history = []
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            data = item.data(Qt.UserRole)
            chat_history.append({
                'role': data['role'],
                'content': data['content']
            })
        return chat_history


def main():
    app = QApplication(sys.argv)
    window = ChatManager()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
