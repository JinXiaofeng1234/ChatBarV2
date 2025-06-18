import re

def clean_llm_response(text: str) -> str:
    """
    清理大模型回复中的动作表情描述
    支持清理：
    - 中文括号（）
    - 英文括号()
    - 中文方括号【】
    - 英文方括号[]
    - 书名号《》
    """
    text = text.replace('\n', '')
    # 匹配所有类型的括号及其内容
    pattern = r'[\(（].*?[\)）]|[\[【].*?[\]】]|《.*?》|\*.*?\*'

    # 替换所有匹配到的内容为空字符串
    cleaned_text = re.sub(pattern, '', text)

    # 去除可能产生的多余空格
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    return cleaned_text


if __name__ == "__main__":
    a = clean_llm_response("""*adjusts his red collar with a smug grin* Oh, you haven't heard? Faster Than the Speed of Love - my critically acclaimed novel. Though I suppose "critically acclaimed" might be stretching it... the New York Times called it "a thing that exists."  *takes sip of martini* But really, it's quite profound. Explores the human condition through canine metaphors. You should pick up a copy - if you can find one. The print run was... limited.""")
    print(a)


