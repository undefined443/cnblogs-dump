import sqlite3
import os
import glob
import time
import datetime


def parse_time(t):
    try:
        return int(time.mktime(datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S").timetuple()))
    except Exception:
        return None


def load_blogs_from_db():
    db_files = glob.glob("cnblogs_blog_*.db")
    if not db_files:
        raise FileNotFoundError("No matching database file found.")
    conn = sqlite3.connect(db_files[0])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blog_Content")
    blogs = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return blogs, columns


def export_blogs_to_markdown(blogs, columns, output_dir="blogs"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for blog in blogs:
        blog_dict = {col: val for col, val in zip(columns, blog)}
        title = blog_dict.get("Title", "Untitled")
        safe_title = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in title).strip()
        filename = f"{blog_dict.get('Id', 'unknown')}_{safe_title}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n")
            f.write(f"<!-- 创建时间: {blog_dict.get('CreatedTime', '')} -->\n")
            f.write(f"<!-- 更新时间: {blog_dict.get('DateUpdated', '')} -->\n")
            f.write(f"<!-- 来源链接: {blog_dict.get('SourceUrl', '')} -->\n")
            f.write(f"<!-- 描述: {blog_dict.get('Description', '')} -->\n\n")

            body = blog_dict.get("Body", "")
            if blog_dict.get("IsMarkdown", 0):
                f.write(body)
            else:
                f.write("```html\n")
                f.write(body)
                f.write("\n```")

        created_time = blog_dict.get("CreatedTime", "")
        updated_time = blog_dict.get("DateUpdated", "")

        ctime = parse_time(created_time)
        mtime = parse_time(updated_time)
        if ctime and mtime:
            os.utime(filepath, (ctime, mtime))
        elif ctime:
            os.utime(filepath, (ctime, ctime))
        elif mtime:
            os.utime(filepath, (mtime, mtime))


def main():
    blogs, columns = load_blogs_from_db()
    export_blogs_to_markdown(blogs, columns)


if __name__ == "__main__":
    main()
