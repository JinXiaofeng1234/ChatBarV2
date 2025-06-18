import yaml

def load_yaml_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            # print(data['DEEPSEEK V3'])
    except yaml.YAMLError as e:
        print(f"YAML解析错误: {e}")
        return None
    except FileNotFoundError:
        print("文件未找到")
        return None
    return data