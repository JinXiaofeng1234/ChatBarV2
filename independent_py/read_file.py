import json
import time
import toml

def get_date_time(pattern):
    # 获取当前时间戳
    now = int(time.time())
    # 转换为本地时间结构体
    time_array = time.localtime(now)
    # 格式化日期
    if pattern == 'file':
        standard_style_time = time.strftime("%Y-%m-%d %H_%M_%S", time_array)
    else:
        standard_style_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return standard_style_time

def read_json(file_name):
    with open(file_name, encoding='utf-8') as user_file:
        file_contents = user_file.read()
    parsed_json = json.loads(file_contents)
    user_file.close()
    return parsed_json

def read_txt(file_name):
    txt_file = open(file_name, encoding='utf-8')
    content = txt_file.read()
    txt_file.close()
    return content

def save_memory_json(dic_data, path):
    # 将字典写入 JSON 文件
    with open(f'{path}/saving/saving-{get_date_time(pattern="file")}.json', 'w', encoding='utf-8') as json_file:
        json.dump(dic_data, json_file, ensure_ascii=False, indent=4)
    json_file.close()
    print("记忆已经保存")

def read_toml(path):
    try:
        with open(path, "r", encoding='utf-8') as f:
            config = toml.load(f)
            return config
    except FileNotFoundError:
        print("config.toml 文件未找到。")
    except Exception as e:
        print(f"读取 TOML 文件时发生错误: {e}")