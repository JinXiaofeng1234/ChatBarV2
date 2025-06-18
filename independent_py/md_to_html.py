import markdown
from pygments.formatters import HtmlFormatter
import re
# import markdown2 as markdown

 # 添加代码块语言标识
def add_lang_tag(match):
    code_block = match.group(0)
    # 尝试从class中提取语言信息
    lang_match = re.search(r'class=".*?language-(\w+)"', code_block)
    lang = lang_match.group(1) if lang_match else 'text'
    return f'<div class="codehilite" data-lang="{lang}">'

def convert_md_to_html(mode, content, md_file_path=''):
    # 配置扩展列表
    extensions = [
        'markdown.extensions.tables',  # 表格
        'markdown.extensions.fenced_code',  # 围栏代码块
        'markdown.extensions.codehilite',  # 代码高亮
        'markdown.extensions.nl2br',  # 换行
        'markdown.extensions.sane_lists',  # 列表处理
        'markdown.extensions.extra',  # 额外特性(包含删除线)
        'markdown.extensions.meta',  # 元数据
        'markdown.extensions.toc',  # 目录
        'markdown.extensions.smarty',  # 智能标点
        'markdown.extensions.wikilinks',  # Wiki链接
        'mdx_gfm'
    ]

    # 配置扩展选项
    extension_configs = {
        'markdown.extensions.codehilite': {
            'css_class': 'codehilite',
            'linenums': True,  # 显示行号
            'guess_lang': True,  # 猜测编程语言
            'use_pygments': True,  # 使用Pygments
            'noclasses': False,  # 使用classes而不是内联样式
        }
    }

    # 生成Pygments CSS
    formatter = HtmlFormatter(style='native', linenos=True)
    pygments_css = formatter.get_style_defs('.codehilite')

    # 添加基础CSS样式
    base_css = """
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        line-height: 1.6;
        padding: 20px;
        max-width: 900px;
        margin: 0 auto;
    }

    /* 删除线样式 */
    del {
        text-decoration: line-through;
        color: #666;
    }

    /* 代码块样式 */
    .codehilite {
        position: relative;
        background-color: #f6f8fa;
        border-radius: 3px;
        margin: 1em 0;
    }

    .codehilite pre {
        padding: 16px;
        overflow: auto;
        line-height: 1.45;
        margin: 0;
    }

    /* 代码块行号样式 */
    .linenos {
        color: #999;
        padding-right: 10px;
        border-right: 1px solid #ddd;
        text-align: right;
        -webkit-user-select: none;
        -moz-user-select: none;
        user-select: none;
    }

    /* 代码块底部语言标识 */
    .codehilite:after {
        content: attr(data-lang);
        position: absolute;
        right: 5px;
        bottom: 5px;
        font-size: 12px;
        color: #666;
        background: #e6e6e6;
        padding: 2px 8px;
        border-radius: 3px;
    }

    /* 其他基础样式 */
    h1, h2, h3, h4, h5, h6 {
        margin-top: 24px;
        margin-bottom: 16px;
        font-weight: 600;
        line-height: 1.25;
    }

    table {
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
    }

    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }

   code {
    background-color: rgba(62, 66, 78, .08); /* 浅灰色背景，稍微透明 */
    border-radius: 3px;                     /* 轻微的圆角 */
    padding: .2em .4em;                     /* 上下0.2em，左右0.4em 的内边距 */
    font-family: SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace; /* 等宽字体 */
    font-size: 85%;                         /* 相对于父元素字体大小的85% */
    color: #333;                            /* 字体颜色 */
}

    blockquote {
        padding: 0 1em;
        color: #6a737d;
        border-left: .25em solid #dfe2e5;
        margin: 0;
    }

    img {
        max-width: 100%;
        height: auto;
    }
    """

    # 处理Markdown内容
    if mode == 0:
        # content = process_strikethrough(content)
        html_body_content = markdown.markdown(
            content,
            extensions=extensions,
            extension_configs=extension_configs
        )
    else:
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                # md_content = process_strikethrough(md_content)
            html_body_content = markdown.markdown(
                md_content,
                extensions=extensions,
                extension_configs=extension_configs
            )
        except Exception as e:
            print(f"转换过程中发生错误：{e}")
            return None



    html_body_content = re.sub(
        r'<div class="codehilite"[^>]*>',
        add_lang_tag,
        html_body_content
    )

    # 生成完整的HTML
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style type="text/css">
            {base_css}
            {pygments_css}
        </style>
    </head>
    <body>
        {html_body_content}
    </body>
    </html>
    """

    return full_html

if __name__ == "__main__":
    # 示例用法
    input_md_file = "input.md"  # 你的Markdown文件路径
    output_html_file = "output.html" # 输出HTML文件路径

    # 创建一个示例Markdown文件用于测试
    with open(input_md_file, 'w', encoding='utf-8') as f:
        f.write("# 这是一个标题\n\n")
        f.write("这是一段**粗体**文本。\n\n")
        f.write("- 列表项1\n")
        f.write("- 列表项2\n")

    convert_md_to_html(input_md_file, output_html_file)