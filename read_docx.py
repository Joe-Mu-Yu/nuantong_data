from docx import Document

# 读取Word文档
doc = Document('d:/Users/joero/Desktop/src/居民住宅供暖室内温度连续测量方法.docx')

# 提取所有段落内容
content = []
for para in doc.paragraphs:
    if para.text.strip():
        content.append(para.text)

# 打印内容
print('\n'.join(content))
