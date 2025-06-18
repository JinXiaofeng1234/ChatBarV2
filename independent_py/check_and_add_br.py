def check_and_add_br(char):
    """
    判断输入字符是否是结束标点符号，如果是，则返回 f'{char}<br>'，
    否则返回原始字符。

    Args:
        char: 需要判断的单个字符。

    Returns:
        如果字符是结束标点符号，则返回带 <br> 的字符串，否则返回原始字符。
    """
    # 定义一个包含常见结束标点符号的集合
    # 英文标点和中文标点都包含
    end_punctuations = {'.', '!', '?', '。', '！', '？'}

    if char in end_punctuations:
        return f'{char}<br>'
    else:
        return char