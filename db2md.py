"""
CNBlogs Dump

Convert cnblogs_blog_*.db to markdown files.


Author: undefined443
Version: 1.2.0
Created Time: 2025-08-15

Usage:
    python db2md.py
"""

import sqlite3
import os
import glob
import time
import datetime
import yaml


def parse_time(t):
    """Parse time string to Unix timestamp.

    Args:
        t (str): Time string, format: "YYYY-MM-DD HH:MM:SS"

    Returns:
        int or None: Unix timestamp, return None if parsing failed

    Example:
        >>> parse_time("2024-01-01 12:00:00")
        1704096000
    """
    try:
        return int(time.mktime(datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S").timetuple()))
    except Exception:
        return None


def load_blogs_from_db():
    """Load blogs from database file.

    Automatically find matching database file (format: cnblogs_blog_*.db),
    and read all blog content and metadata.

    Returns:
        tuple: (blogs, columns)
            - blogs: blog content list, each element is a row data
            - columns: database column name list

    Raises:
        FileNotFoundError: When no matching database file is found

    Example:
        >>> blogs, columns = load_blogs_from_db()
        >>> print(f"Found {len(blogs)} blogs")
    """
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
    """Export blogs to Markdown files.

    Create separate Markdown files for each blog, including:
    - Title as filename (automatically handle special characters)
    - Metadata as HTML comments (created time, updated time, source link, description)
    - Blog content
    - Preserve original file timestamp

    Args:
        blogs (list): blog content list, each element is a row data
        columns (list): database column name list
        output_dir (str, optional): output directory, default is "blogs"

    Example:
        >>> blogs, columns = load_blogs_from_db()
        >>> export_blogs_to_markdown(blogs, columns, "my_blogs")

    Note:
        - Automatically create output directory (if not exists)
        - File name format: {ID}_{Title}.md
        - Special characters will be replaced with underscores
        - Support HTML and Markdown format blog content
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for blog_row in blogs:
        blog = dict(zip(columns, blog_row))
        front_matter = {
            'id': blog['Id'],
            'title': blog['Title'],
            'date': blog['DateAdded'],
            'updated': blog['DateUpdated'],
            'blog_id': blog['BlogId'],
            'post_type': blog['PostType'],
            'is_markdown': bool(blog['IsMarkdown']),
            'is_active': bool(blog['IsActive']),
            'access_permission': blog['AccessPermission']
        }

        if blog['SourceUrl']:
            front_matter['source_url'] = blog['SourceUrl']
        if blog['Description']:
            front_matter['description'] = blog['Description']
        if blog['EntryName']:
            front_matter['entry_name'] = blog['EntryName']
        if blog['CreatedTime']:
            front_matter['created_time'] = blog['CreatedTime']
        if blog['AutoDesc']:
            front_matter['auto_desc'] = blog['AutoDesc']

        content = f"---\n{yaml.dump(front_matter, default_flow_style=False, allow_unicode=True)}---\n{blog['Body']}"

        filename = f"{front_matter['id']}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        created_time = blog.get("CreatedTime", "")
        updated_time = blog.get("DateUpdated", "")

        ctime = parse_time(created_time)
        mtime = parse_time(updated_time)
        if ctime and mtime:
            os.utime(filepath, (ctime, mtime))
        elif ctime:
            os.utime(filepath, (ctime, ctime))
        elif mtime:
            os.utime(filepath, (mtime, mtime))


def main():
    """Main function, execute blog export process.

    Execute complete blog export process:
    1. Load blog content from database
    2. Export to Markdown file
    3. Preserve original timestamp

    Example:
        >>> main()
        # Start exporting blogs...
    """
    blogs, columns = load_blogs_from_db()
    export_blogs_to_markdown(blogs, columns)


if __name__ == "__main__":
    main()
