"""Publisher HTML 模板"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        :root {
            --primary-color: #1a365d;
            --secondary-color: #2c5282;
            --text-color: #2d3748;
            --bg-color: #ffffff;
            --border-color: #e2e8f0;
            --link-color: #3182ce;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, "Noto Sans SC", sans-serif;
            line-height: 1.8;
            color: var(--text-color);
            background-color: #f7fafc;
            padding: 2rem;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: var(--bg-color);
            padding: 3rem 4rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }

        h1 {
            color: var(--primary-color);
            font-size: 2rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 3px solid var(--primary-color);
        }

        h2 {
            color: var(--secondary-color);
            font-size: 1.5rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        h3 {
            color: var(--secondary-color);
            font-size: 1.25rem;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }

        p {
            margin-bottom: 1rem;
            text-align: justify;
        }

        a {
            color: var(--link-color);
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        /* 引用样式 */
        sup {
            font-size: 0.75rem;
            color: var(--link-color);
        }

        sup a {
            color: inherit;
        }

        /* 表格样式 */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
        }

        th, td {
            padding: 0.75rem 1rem;
            text-align: left;
            border: 1px solid var(--border-color);
        }

        th {
            background-color: var(--primary-color);
            color: white;
            font-weight: 600;
        }

        tr:nth-child(even) {
            background-color: #f8fafc;
        }

        /* 代码块 */
        code {
            background-color: #edf2f7;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: "SFMono-Regular", Consolas, monospace;
            font-size: 0.9rem;
        }

        pre {
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }

        pre code {
            background: none;
            padding: 0;
            color: inherit;
        }

        /* 引用块 */
        blockquote {
            border-left: 4px solid var(--primary-color);
            padding-left: 1rem;
            margin: 1rem 0;
            color: #4a5568;
            font-style: italic;
        }

        /* 列表 */
        ul, ol {
            margin: 1rem 0;
            padding-left: 2rem;
        }

        li {
            margin-bottom: 0.5rem;
        }

        /* 参考文献 */
        .references {
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 2px solid var(--border-color);
        }

        .references h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
        }

        .references p {
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
            padding-left: 2rem;
            text-indent: -2rem;
        }

        /* 页脚 */
        .footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: #718096;
            font-size: 0.875rem;
        }

        /* 打印样式 */
        @media print {
            body {
                background: none;
                padding: 0;
            }

            .container {
                box-shadow: none;
                padding: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        {{ content }}

        {% if sources %}
        <div class="references">
            <h2>参考文献</h2>
            {% for source in sources %}
            <p>{{ source }}</p>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            <p>由 DeepFinance 生成 | {{ generated_at }}</p>
        </div>
    </div>
</body>
</html>
"""

PDF_CSS = """
@page {
    size: A4;
    margin: 2.5cm;

    @top-center {
        content: "{{ title }}";
        font-size: 10pt;
        color: #666;
    }

    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 10pt;
        color: #666;
    }
}

body {
    font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 11pt;
    line-height: 1.6;
}

h1 {
    page-break-after: avoid;
}

h2, h3 {
    page-break-after: avoid;
}

table {
    page-break-inside: avoid;
}

.references {
    page-break-before: always;
}
"""
