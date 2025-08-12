import sqlite3
import os
import glob

db_files = glob.glob("cnblogs_blog_*.db")
conn = sqlite3.connect(db_files[0])
cursor = conn.cursor()
cursor.execute("SELECT * FROM blog_Content")
blogs = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

output_dir = "blogs"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for blog in blogs:
    blog_dict = {col: val for col, val in zip(columns, blog)}
    title = blog_dict.get('Title', 'Untitled')
    safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in title).strip()
    filename = f"{blog_dict.get('Id', 'unknown')}_{safe_title}.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n")
        f.write(f"<!-- 创建时间: {blog_dict.get('CreatedTime', '')} -->\n")
        f.write(f"<!-- 更新时间: {blog_dict.get('DateUpdated', '')} -->\n")
        f.write(f"<!-- 来源链接: {blog_dict.get('SourceUrl', '')} -->\n")
        f.write(f"<!-- 描述: {blog_dict.get('Description', '')} -->\n\n")

        body = blog_dict.get('Body', '')
        if blog_dict.get('IsMarkdown', 0):
            f.write(body)
        else:
            f.write("```html\n")
            f.write(body)
            f.write("\n```")

conn.close()
