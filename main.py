import os
import sys
import pathlib
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QTextEdit, QLabel,
    QSizePolicy, QFileDialog, QScrollArea, QDialog
)
from PyQt5.QtCore import Qt, QThread, QTimer, QEvent
from PyQt5.QtGui import QFont, QTextCursor, QTextOption # 引入 QTextCursor

from llm_worker import LLMWorker, ChatWithLLM
from tts_worker import synthesis_sound_async
from folder_manager import list_files_sorted_by_time
from response_clear import clean_llm_response

from read_file import read_json, save_memory_json, read_toml
from md_to_html import convert_md_to_html
from check_and_add_br import check_and_add_br

from custom_button import custom_buttom_with_img
from custom_combo_box import model_combo_box
from load_yaml import load_yaml_file

from modify_llm_response_window import TextEditorDialog
from setting_menu import SettingMenu
from live2d_model_param_modifier import Live2DParamModifier
from folder_selector import FolderSelector
from ChatManager import ChatManager

# 假设你的 Live2DOpenGLWidget 已经在一个名为 live2d_widget.py 的文件中
# 如果 Live2DOpenGLWidget 导致崩溃，暂时用 QWidget 替代以测试主程序逻辑
try:
    from live2d_widget import Live2DOpenGLWidget, Live2DModel
    # raise ImportError
except ImportError:
    print("live2d_widget.py not found or has issues, using a dummy QWidget instead.")
    class Live2DOpenGLWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setStyleSheet("background-color: #333333;") # 假装 Live2D 背景
            # 模拟 live2d_model 属性，避免运行时错误
            class DummyLive2DModel:
                audio_played = False
            self.live2d_model = DummyLive2DModel()


class MainWindow(QMainWindow):
    def __init__(self, role_card):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()  # 尝试在窗口显示后立即设置焦点
        QApplication.instance().installEventFilter(self)
        self.role_card_path = role_card
        self._load_api()
        self._init_role()

        self.setWindowTitle("ChatBarV2")

        self.sound_play_keeper = QTimer(self)
        self.sound_play_keeper.setInterval(2000)
        self.sound_play_keeper.timeout.connect(self.tts_sound_file_checker)
        self.sound_play_keeper.start()

        self.setGeometry(100, 100, 1920, 1000)
        # self.setFixedSize(1920, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.live2d_widget = Live2DOpenGLWidget(self, live2d_model_path=self.role_model_path,
                                                audio_path=self.latest_sound_file,
                                                bg_path=self.bg_path)
        self.live2d_widget.setFixedSize(1200, 1000)
        main_layout.addWidget(self.live2d_widget)


        dialog_container = QWidget()
        dialog_container.setObjectName("dialog_container")
        dialog_container.setFixedSize(720, 1000)
        main_layout.addWidget(dialog_container)

        dialog_layout = QVBoxLayout(dialog_container)
        dialog_layout.setContentsMargins(20, 20, 20, 20)
        dialog_layout.setSpacing(10)

        role_label_layout = QHBoxLayout()
        self.character_name_label = QLabel(f"〖{self.role_name}〗")
        self.character_name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.character_name_label.setFont(QFont("幼圆", 18, QFont.Bold))
        self.character_name_label.setObjectName("characterNameLabel")

        role_label_layout.addWidget(self.character_name_label)

        self.tts_model_combo = model_combo_box(self.tts_api_data)
        role_label_layout.addWidget(self.tts_model_combo)

        self.params_modify_btn = custom_buttom_with_img('imgs/icon/params.png', 50, 50)
        self.params_modify_btn.clicked.connect(self.params_modify_func)
        role_label_layout.addWidget(self.params_modify_btn)

        self.role_switch_btn = custom_buttom_with_img('imgs/icon/role_switch_icon.png', 50, 50)
        self.role_switch_btn.clicked.connect(self.swtich_role)
        role_label_layout.addWidget(self.role_switch_btn)

        self.setting_btn = custom_buttom_with_img('imgs/icon/setting_icon.png', 50, 50)
        self.setting_btn.clicked.connect(self.get_setting)
        role_label_layout.addWidget(self.setting_btn)

        dialog_layout.addLayout(role_label_layout)
        # 创建一个QTextOption对象
        option = QTextOption()
        # 设置换行模式为WordWrap
        option.setWrapMode(QTextOption.WrapMode.WrapAnywhere)

        self.dialog_text_display = QTextEdit()
        # 将QTextOption设置到QTextEdit的QTextDocument中
        self.dialog_text_display.document().setDefaultTextOption(option)
        self.dialog_text_display.setReadOnly(True)
        self.dialog_text_display.setHtml(convert_md_to_html(0, self.latest_response))
        self.dialog_text_display.setFont(QFont("微软雅黑", 14))
        self.dialog_text_display.setObjectName("dialogTextDisplay")
        self.dialog_text_display.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical { border: 1px solid #999999; background: #555555; width: 10px; margin: 0px; }
            QScrollBar::handle:vertical { background: #888888; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        dialog_layout.addWidget(self.dialog_text_display)

        top_controls_layout = QHBoxLayout()
        # 下拉框
        self.llm_selector = model_combo_box(self.llm_api_data)
        self.llm_selector.setCurrentIndex(0)
        top_controls_layout.addWidget(self.llm_selector)
        self.llm_selector.currentIndexChanged.connect(self.change_llm_api)

        self.llm_api_add_btn = custom_buttom_with_img('imgs/icon/add_llm_api_btn.png', 50, 50)
        top_controls_layout.addWidget(self.llm_api_add_btn)

        # 上传文件按钮
        self.upload_file_button = custom_buttom_with_img('imgs/icon/image_outline_icon.png', 50, 50)
        self.upload_file_button.clicked.connect(self.upload_file)
        top_controls_layout.addWidget(self.upload_file_button)

        top_controls_layout.addStretch(1) # 中间留空

        # 右边两个按钮
        self.extened_tool = custom_buttom_with_img('imgs/icon/equalizer.png', 50, 50)
        top_controls_layout.addWidget(self.extened_tool)

        self.select_conversation_history_button = custom_buttom_with_img('imgs/icon/conversation_selector_icon.png', 50, 50)
        self.select_conversation_history_button.clicked.connect(self.conversation_history_manager)
        top_controls_layout.addWidget(self.select_conversation_history_button)

        self.conversation_history_save_button = custom_buttom_with_img('imgs/icon/conversation_save_icon.png', 50, 50)
        top_controls_layout.addWidget(self.conversation_history_save_button)

        dialog_layout.addLayout(top_controls_layout)
        # --- 顶部控制区域结束 ---


        # --- user_input_edit 和左侧按钮的新布局 ---
        input_and_buttons_layout = QHBoxLayout()

        # 创建一个 QScrollArea
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedSize(80, 200)
        # 创建一个 QWidget 作为滚动区域的内容容器
        content_widget = QWidget()
        content_widget.setObjectName("scrollAreaContent")
        scroll_area.setWidget(content_widget)
        # 左侧垂直布局用于放置发送和语音按钮
        left_buttons_layout = QVBoxLayout(content_widget)

        self.send_button = custom_buttom_with_img('imgs/icon/send_icon.png', 50, 50)
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_info_to_llm) # 仍连接到原来的槽函数
        self.send_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding) # 按钮大小策略，让其能填充垂直空间
        left_buttons_layout.addWidget(self.send_button)

        self.voice_button = custom_buttom_with_img('imgs/icon/sound_icon.png', 50, 50)
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.clicked.connect(self.on_voice_button_clicked) # 新增语音按钮的槽函数
        self.voice_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding) # 按钮大小策略
        left_buttons_layout.addWidget(self.voice_button)

        self.translate_button = custom_buttom_with_img('imgs/icon/translate.png', 50, 50)
        self.translate_button.clicked.connect(self.translate_to_chinese)
        self.translate_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 按钮大小策略
        left_buttons_layout.addWidget(self.translate_button)

        self.repeat_button = custom_buttom_with_img('imgs/icon/repeat_icon.png', 50, 50)
        self.repeat_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 按钮大小策略
        self.repeat_button.clicked.connect(self.llm_repeat_func)
        left_buttons_layout.addWidget(self.repeat_button)

        self.modify_llm_response_btn = custom_buttom_with_img('imgs/icon/modify_llm_response_icon.png', 50, 50)
        self.modify_llm_response_btn.clicked.connect(self.modify_llm_response)
        left_buttons_layout.addWidget(self.modify_llm_response_btn)

        self.fromat_conversation_history_btn = custom_buttom_with_img('imgs/icon/format.png', 50, 50)
        self.fromat_conversation_history_btn.clicked.connect(lambda :self.format_conversation_history(False))

        self.clear_history_button = custom_buttom_with_img('imgs/icon/delete.png', 50, 50)
        self.clear_history_button.clicked.connect(lambda :self.format_conversation_history(True))

        left_buttons_layout.addWidget(self.fromat_conversation_history_btn)
        left_buttons_layout.addWidget(self.clear_history_button)

        input_and_buttons_layout.addWidget(scroll_area)

        self.user_input_edit = QTextEdit()
        self.user_input_edit.setPlaceholderText("在这里输入你的回复...")
        self.user_input_edit.setFont(QFont("幼圆", 12))
        self.user_input_edit.setObjectName("userInputLine")
        self.user_input_edit.setFixedSize(600, 200)
        input_and_buttons_layout.addWidget(self.user_input_edit)

        dialog_layout.addLayout(input_and_buttons_layout)


        self.apply_galgame_style()

        self.llm_thread = None
        self.llm_worker = None

        # self._init_params_modifier()
        # print(self.bg_path)
        # self.live2d_widget._load_bg(self.bg_path)

    def _load_api(self):
        self.llm_api_data = load_yaml_file('api_key/llm_api_key.yaml')
        self.llm_model_ls = list(self.llm_api_data.keys())

        self.tts_api_data = load_yaml_file('api_key/tts_api_key.yaml')
        self.tts_model_ls = list(self.llm_api_data.keys())

    def _init_role(self):
        self.llm_repeat_flag = False
        self.tool_use_flag = False
        self.native_tokens = str()
        self.full_response = str()
        self.user_text_backup = str()
        self.conversation_history = list()
        self.token_num = int()

        llm_model_parameter = self.llm_api_data[self.llm_model_ls[0]]
        self.model_manager = ChatWithLLM(init_api=llm_model_parameter["api_key"],
                                        init_url=llm_model_parameter["base_url"],
                                        init_model_name=llm_model_parameter["model_name"])


        bg_ls = os.listdir(f'{self.role_card_path}/bg')
        self.setting_menu_dialog = SettingMenu(self, width=1920, height=1000,
                                               bg_ls=bg_ls)  # 将主窗口作为父级传递
        self.bg_path = f'{self.role_card_path}\\bg\\{bg_ls[0]}'
        role_json = read_json(f'{self.role_card_path}/role.json')
        self.role_name = role_json["role_name"]
        self.role_model_path = role_json["model_path"]
        prompt = role_json["prompt"]
        opening_statement = role_json["opening_statement"]
        self.latest_response = opening_statement
        tts_setting_json = read_json(f'{self.role_card_path}/tts_setting/tts_setting.json')
        self.refer_txt = tts_setting_json["txt"]
        self.minmax_role_key = tts_setting_json["minmax_role_key"]
        self.fish_role_key = tts_setting_json["fish_role_key"]
        # 检查存档
        memory_ls = list_files_sorted_by_time(rf'{self.role_card_path}/saving')
        if not memory_ls:
            self.conversation_history.append({"role": "system", "content": prompt})
            self.conversation_history.append({"role": "user", "content": opening_statement})
        else:
            if len(memory_ls) == 1:
                self.latest_saving = read_json(memory_ls[0])
            else:
                self.latest_saving = read_json(memory_ls[-1])
            self.conversation_history = self.latest_saving["memory"]
            self.token_num = self.latest_saving["token"]
            self.latest_response = self.conversation_history[-1]['content']
            self.bg_path = f'{self.role_card_path}\\bg\\{self.latest_saving["bg_name"]}'

        self.conversation_history_original_length = len(self.conversation_history)
        if self.conversation_history_original_length > 2:
            self.user_text_backup = self.conversation_history[-2]['content']
            self.full_response = self.conversation_history[-1]['content']

        self.tokens = str()
        self.latest_sound_file = str(list_files_sorted_by_time(f'{self.role_card_path}/tmp_audio')[-1])

    def _init_params_modifier(self):
        self.params_modify = Live2DParamModifier(self.live2d_widget.live2d_model.param_dic, self.live2d_widget.live2d_model)

    def swtich_role(self):
        role_cards_path = FolderSelector().get_folder_path('role_cards')
        if role_cards_path and self.role_card_path != role_cards_path:
            self.app_shut_down_func()  # 保存记忆
            self.role_card_path = role_cards_path
            self.latest_saving = None  # 清空此前角色存档
            self.token_num = None  # 清空token计数
            self._init_role()  # 初始化人物卡
            self.character_name_label.setText(f'【{self.role_name}】')
            self.dialog_text_display.setHtml(convert_md_to_html(0, self.latest_response))
            self.live2d_widget._load_bg(self.bg_path)
            self.live2d_widget.live2d_model = Live2DModel(self.role_model_path, self.live2d_widget.width(),
                                                          self.live2d_widget.height(),
                                                          self.latest_sound_file)
        #     # play_sound_async(self.role_cards_path)  # 播放欢迎语句

    def conversation_history_manager(self):
        # print(self.conversation_history)
        result = ChatManager(self.conversation_history, self).exec_()
        self.conversation_history_original_length = len(self.conversation_history)

    def params_modify_func(self):
        self._init_params_modifier()
        result = self.params_modify.exec_()

    def get_setting(self):
        # show()是非模态，exec_()是模态
        # 如果是模态对话框，这里会阻塞，直到对话框关闭
        result = self.setting_menu_dialog.exec_()

        if result == QDialog.Accepted:
            self.bg_path = pathlib.Path(self.role_card_path, 'bg', self.setting_menu_dialog.get_selected_background()[0])
            self.live2d_widget._load_bg(self.bg_path)
            print(self.bg_path)
        else:
            print("小对话框被用户关闭了 (Rejected 或其他)。")

    def format_conversation_history(self, double_clicked):
        if not double_clicked and len(self.conversation_history) > 9:
            self.conversation_history = self.conversation_history[:2] + self.conversation_history[-5:]
        else:
            if len(self.conversation_history) > 3:
                self.conversation_history = self.conversation_history[0:2]
        self.conversation_history_original_length = len(self.conversation_history)
        # print(self.conversation_history)

    def translate_to_chinese(self):
        if self.full_response:
            self.tool_use_flag = True
            self._init_llm_worker(clear_input_flag=False)
            prompt = [read_toml('tool_prompt/translate.toml')['prompt'],
                      {"role": "user", "content": self.full_response}]
            response_obj = self.model_manager.get_llm_response(prompt)
            self._output_response(response_obj)

    def modify_llm_response(self):
        dialog = TextEditorDialog(self, default_text=self.conversation_history[-1]['content'],
                                  width=1920, height=1000) # 将主窗口作为父级传递
        # show()是非模态，exec_()是模态
        # 如果是模态对话框，这里会阻塞，直到对话框关闭
        result = dialog.exec_()

        if result == QDialog.Accepted:
            result_text = dialog.get_text()
            if result_text and result_text != self.conversation_history[-1]['content']:
                self.conversation_history[-1]['content'] = result_text
        else:
            print("小对话框被用户关闭了 (Rejected 或其他)。")

    def llm_repeat_func(self):
        self.send_info_to_llm(text=self.user_text_backup)
        self.llm_repeat_flag = True


    def app_shut_down_func(self):
        conversation_history_current_length = len(self.conversation_history)
        if conversation_history_current_length > 2 \
                and conversation_history_current_length > self.conversation_history_original_length:
            saving = {
                      "bg_name": str(self.bg_path).split('\\')[-1],
                      "memory": self.conversation_history,
                      "token": self.token_num
            }
            save_memory_json(saving, self.role_card_path)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            # 无论焦点在哪里，只要是键盘按下事件，都让 MainWindow 的 keyPressEvent 处理
            self.keyPressEvent(event)
            return False  # 表示事件已被处理，不再向其他对象传播
        elif event.type() == QEvent.KeyRelease: # 新增：处理按键释放事件
            self.keyReleaseEvent(event)
            return False
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """
            捕获键盘按下事件
            """
        """
          捕获键盘按下事件
          """
        if event.key() == Qt.Key_Enter:
            self.send_info_to_llm()

    def closeEvent(self, a0):
        self.app_shut_down_func()

    def tts_sound_file_checker(self):
        sorted_folder_path_ls = list_files_sorted_by_time(f'{self.role_card_path}/tmp_audio')
        latest_sound_file = str(sorted_folder_path_ls[-1])
        if self.latest_sound_file != latest_sound_file and 'tmp.mp3' not in latest_sound_file:
            self.latest_sound_file = latest_sound_file
            self.live2d_widget.live2d_model.audio_path = self.latest_sound_file
            self.live2d_widget.live2d_model.audio_played = False

    def change_llm_api(self):
        selected_index = self.llm_selector.currentIndex()
        if self.llm_api_data:
            llm_model_parameter = self.llm_api_data[self.llm_model_ls[selected_index]]
            self.model_manager.rebuild_llm_client(int(llm_model_parameter['mode']),
                                                  llm_model_parameter["api_key"],
                                                  llm_model_parameter["base_url"],
                                                  llm_model_parameter["model_name"])



    def send_info_to_llm(self, text=None):
        print('激活发送信息事件')
        user_text = self.user_input_edit.toPlainText() if not text else text
        self.user_text_backup = user_text
        if not user_text.strip():
            return

        self._init_llm_worker()

        # 模拟角色流式回复的完整 HTML 文本
        self.conversation_history.append({"role": "user", "content": user_text})
        response_object = self.model_manager.get_llm_response(self.conversation_history)
        self._output_response(response_object)

    def _output_response(self, response_object):
        self.llm_thread = QThread()
        self.llm_worker = LLMWorker(response_object)
        self.llm_worker.moveToThread(self.llm_thread)
        self.llm_thread.started.connect(self.llm_worker.run)
        self.llm_worker.new_token_received.connect(self.update_llm_text_display)
        self.llm_worker.response_finished.connect(self.llm_response_finished)
        self.llm_worker.error_occurred.connect(self.llm_error_occurred)
        self.llm_thread.start()
        self.send_button.setEnabled(False)
        self.user_input_edit.setEnabled(False)

    def _init_llm_worker(self, clear_input_flag=True):
        # 如果有正在进行的流式输出，停止它并清空
        if self.llm_thread and self.llm_thread.isRunning():
            self.llm_worker.stop()
            self.llm_thread.quit()
            self.llm_thread.wait()  # 确保线程完全停止
            self.llm_thread = None
            self.llm_worker = None
            # 可以在这里处理未完成的文本，但为了简单，这里直接清除，新消息会覆盖
        if clear_input_flag:
            self.user_input_edit.clear()
        # 清空 QtextEdit，准备新的流式输出
        self.dialog_text_display.clear()  # 清除之前的文本，只显示最新对话

    def upload_file(self):
        print("上传文件按钮被点击了！")
        # 实现文件选择对话框
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "选择文件", "", "所有文件 (*.*)")
        if file_path:
            print(f"选择了文件: {file_path}")

    def on_voice_button_clicked(self):
        print("语音按钮被点击了！")
        # 实现语音输入/输出逻辑

    def update_llm_text_display(self, token):
        self.native_tokens += token
        cursor = self.dialog_text_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        token = token.replace(" ", "&nbsp;") if " " in token else token
        token = token.replace('\n', '<br>') if '\n' in token else token
        self.tokens += token
        cursor.insertHtml(token)
        self.dialog_text_display.setTextCursor(cursor)
        self.dialog_text_display.setHtml(self.tokens)
        self.dialog_text_display.verticalScrollBar().setValue(self.dialog_text_display.verticalScrollBar().maximum())


    def llm_response_finished(self, full_response, total_tokens):
        if not self.tool_use_flag:
            self.token_num = total_tokens
            self.conversation_history.append({"role": "assistant", "content": full_response})
        full_response_backup = self.full_response
        self.full_response = full_response
        print("大模型回复完成")
        if self.llm_thread:
            self.llm_thread.quit()
            self.llm_thread.wait()
            self.llm_thread = None
            self.llm_worker = None
        self.send_button.setEnabled(True)
        self.user_input_edit.setEnabled(True)
        self.dialog_text_display.clear()
        self.native_tokens = f'{self.native_tokens}\n\n---\n\n{full_response_backup}' if self.tool_use_flag else self.native_tokens
        html_content = convert_md_to_html(0, self.native_tokens)
        self.dialog_text_display.setHtml(html_content)
        self.tokens = str()
        self.native_tokens = str()
        if not self.tool_use_flag:
            filtered_response = clean_llm_response(full_response)
            synthesis_sound_async(0, self.role_card_path, filtered_response, self.fish_role_key,
                  f'{self.role_card_path}/tts_setting/example.mp3',
                  self.refer_txt)
        if self.llm_repeat_flag:
            new_response = self.conversation_history[-1]['content']
            self.conversation_history.pop(-1)
            self.conversation_history[-1]['content'] = new_response
            self.llm_repeat_flag = False
        self.tool_use_flag = False if self.tool_use_flag else self.tool_use_flag

    def llm_error_occurred(self, error_message):
        print(f"大模型请求错误: {error_message}")
        self.dialog_text_display.append(f"<span style='color:red;'>错误: {error_message}</span>")
        self.llm_response_finished("", 0)

    def apply_galgame_style(self):
        style_sheet = read_json('style_sheet.json')["style_sheet"]
        self.setStyleSheet(style_sheet)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(role_card='role_cards/japanese university student')
    window.show()
    sys.exit(app.exec_())