from PyQt5.QtCore import pyqtSignal, QObject
from openai_format import chat_with_openai_like_llm
import json



class ChatWithLLM:
    def __init__(self, specification=0, init_api=str(), init_url=str(), init_model_name=str()):
        self.client = self.create_llm_service(specification, init_api, init_url)
        self.model_name = init_model_name
    def rebuild_llm_client(self, specification, api_key, base_url, model_name):
        self.client = self.create_llm_service(specification, api_key, base_url)
        self.model_name = model_name

    @staticmethod
    def create_llm_service(mode=0, api_key='', base_url=''):
        if mode == 0:
            llm_model = chat_with_openai_like_llm(api_key, base_url)
        return llm_model

    def get_llm_response(self, conversation_history):
        try:
            stream_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=conversation_history,
                stream=True
            )
            return stream_response
        except Exception as e:
            print(e, '网络请求失败')
            return None

# 大模型工作线程
class LLMWorker(QObject):
    new_token_received = pyqtSignal(str) # 每次接收一个字符（或HTML片段）就发送
    response_finished = pyqtSignal(str, int)     # 响应完成时发送
    error_occurred = pyqtSignal(str)     # 发生错误时发送

    def __init__(self, stream_response_obeject, parent=None):
        super().__init__(parent)
        self.total_tokens = 0
        self.full_response = str()
        self.stream_response_obeject = stream_response_obeject
        self._running = True

    def run(self):
        json_content = None
        if self.stream_response_obeject is None:
            return
        for chunk in self.stream_response_obeject:
            if not self._running:
                break
            try:
                    json_content = json.loads(chunk.model_dump_json())
                    content = json_content['choices'][0]['delta']['content']
                    # print(content, end="", flush=True)
                    self.new_token_received.emit(content)
                    self.full_response += content
            except Exception as e:
                ...
        if json_content:
            tokens = json_content['usage']['total_tokens']
            self.total_tokens += tokens
            print(self.total_tokens)
        self.response_finished.emit(self.full_response, self.total_tokens)

    def stop(self):
        self._running = False