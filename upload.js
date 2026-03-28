/**
 * CNBlogs Dump
 *
 * Update cnblogs with local Markdown file.
 *
 * Author: undefined443
 * Version: 1.2.0
 * Created Time: 2025-08-15
 */

import fs from 'fs/promises'
import path from 'path'
import yaml from 'js-yaml'
import axios from 'axios'
import dotenv from 'dotenv'
import sqlite3 from 'sqlite3'
import { open } from 'sqlite'
import { glob } from 'glob'

dotenv.config()

async function getBlogsFromDb(dbPath) {
    /**
     * 从 SQLite 数据库中读取博客文章信息。
     *
     * @param {string} dbPath - 数据库文件路径
     * @returns {Promise<Array<Object>>} 文章列表
     */
    const db = await open({
        filename: dbPath,
        driver: sqlite3.Database,
    })
    const rows = await db.all('SELECT * FROM blog_Content')
    await db.close()
    return rows
}

async function extractFrontMatter(content) {
    /**
     * 解析 Markdown 文件，提取 front matter 和正文内容。
     *
     * @param {string} content - 包含 front matter 的 Markdown 文件内容
     * @returns {Promise<{meta: object, body: string}>} 解析结果，meta 为 front matter 对象，body 为正文
     * @throws {Error} 如果 front matter 格式无效
     */
    const parts = content.split(/^---\s*$/m)
    if (parts.length < 3) throw new Error('Invalid front matter')
    return {
        meta: yaml.load(parts[1]),
        body: parts.slice(2).join('---\n'),
    }
}

function escapeXml(str) {
    /**
     * 对字符串进行 XML 转义，防止特殊字符破坏 XML 格式。
     *
     * @param {string} str - 需要转义的字符串
     * @returns {string} 已转义的字符串
     */
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\r?\n/g, '&#x000A;')
}

async function updatePost(filePath) {
    /**
     * 更新指定博客的内容。
     *
     * 通过 metaWeblog.editPost 接口将内容更新到远程博客。
     *
     * @param {string} filePath - 本地 Markdown 文件路径
     * @returns {Promise<void>}
     */

    const raw = await fs.readFile(filePath, 'utf-8')
    const { meta, body } = await extractFrontMatter(raw)
    const title = meta.title
    const username = process.env.USERNAME || '' // 用户名
    const token = process.env.TOKEN || '' // metaweblog 令牌
    const url = `https://rpc.cnblogs.com/metaweblog/${username}`
    const description = escapeXml(body)
    const data = `<?xml version="1.0"?>
<methodCall>
  <methodName>metaWeblog.editPost</methodName>
  <params>
    <param><value><string>${meta['id']}</string></value></param>
    <param><value><string>${username}</string></value></param>
    <param><value><string>${token}</string></value></param>
    <param>
      <value>
        <struct>
          <member>
            <name>description</name>
            <value><string>${description}</string></value>
          </member>
          <member>
            <name>title</name>
            <value><string>${title}</string></value>
          </member>
          <member>
            <name>categories</name>
            <value>
              <array><data><value><string>[Markdown]</string></value></data></array>
            </value>
          </member>
        </struct>
      </value>
    </param>
    <param><value><boolean>1</boolean></value></param>
  </params>
</methodCall>`

    const response = await axios.post(url, data, {
        headers: { 'Content-Type': 'text/xml' },
    })
    console.log(`Updated post ${meta['id']}:`, response.status)
}

async function main() {
    const dbFiles = glob.sync('cnblogs_blog_*.db')
    if (dbFiles.length === 0) {
        console.error('No database file matching cnblogs_*.db was found')
        process.exit(1)
    }
    const dbPath = dbFiles[0]
    const blogs = await getBlogsFromDb(dbPath)

    for (const blog of blogs) {
        const postId = blog['Id']
        const filePath = path.resolve('blogs/' + postId + '.md')

        try {
            const stats = await fs.stat(filePath)
            const fileModifiedTime = stats.mtime
            const dbUpdatedTime = new Date(blog['DateUpdated'])

            // 只有文件修改时间比数据库时间新时才更新
            if (fileModifiedTime > dbUpdatedTime) {
                console.log(`File ${postId} has been modified, updating...`)
                await updatePost(filePath)
            } else {
                // console.log(`File ${post_id} is up to date, skipping...`);
            }
        } catch (err) {
            console.error(`Error processing ${postId}:`, err.message)
        }
    }
}

main().catch(console.error)
