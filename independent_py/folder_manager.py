from pathlib import Path


def list_files_sorted_by_time(directory):
    # 使用 Pathlib 获取目录中的所有文件
    files = [f for f in Path(directory).iterdir() if f.is_file()]

    if files:

        # 按照最后修改时间对文件进行排序
        files_sorted = sorted(files, key=lambda f: f.stat().st_mtime)

        return files_sorted
    else:
        return None