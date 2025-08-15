/**
 * CNBlogs Substitute Image URLs
 *
 * Substitute image URLs in Markdown files.
 *
 * Author: undefined443
 * Version: 1.0.0
 * Created Time: 2025-08-16
 */

import fs from 'fs/promises'
import fsSync from 'fs'
import path from 'path'
import { glob } from 'glob'
import https from 'https'
import dotenv from 'dotenv'

dotenv.config()

// 下载 CNBlogs 图片
async function downloadImage(url) {
    try {
        await fs.mkdir('image-hosting', { recursive: true })

        // 提取文件名并删除2778973-前缀
        let filename = path.basename(url)
        // filename = filename.replace(/^2778973-/, '');
        const filePath = path.join('image-hosting', filename)

        // 检查文件是否已存在
        try {
            await fs.access(filePath)
            console.log(`File already exists: ${filename}`)
            return
        } catch {
            // pass
        }

        console.log(`Downloading: ${url}`)

        return new Promise((resolve, reject) => {
            const file = fsSync.createWriteStream(filePath)
            https
                .get(url, (response) => {
                    if (response.statusCode === 200) {
                        response.pipe(file)
                        file.on('finish', () => {
                            file.close()
                            console.log(`Downloaded: ${filename}`)
                            resolve()
                        })
                    } else {
                        reject(new Error(`HTTP ${response.statusCode}: ${url}`))
                    }
                })
                .on('error', (err) => {
                    fsSync.unlinkSync(filePath)
                    reject(err)
                })
        })
    } catch (error) {
        console.error(`Error downloading ${url}:`, error.message)
    }
}

async function substituteImageUrls() {
    const blogsDir = 'blogs'
    try {
        await fs.access(blogsDir)
    } catch {
        console.log('blogs directory does not exist.')
        return
    }

    // const pattern_full = /https:\/\/img2024.cnblogs.com\/blog\/2778973\/\d+\/2778973-.*\.\w+/g;
    // const pattern_sub = /img2024\.cnblogs\.com\/blog\/2778973\/\d+\/2778973-/g;
    const pattern_full = /https:\/\/s2.loli.net\/\d+\/\d+\/\d+\/\w+\.\w+/g
    const pattern_sub = /s2.loli.net\/\d+\/\d+\/\d+\//g
    const endpoint = process.env.ENDPOINT
    const replacement = `${endpoint}/image-hosting/`
    let modifiedCount = 0

    try {
        const mdFiles = await glob('blogs/*.md')
        for (const mdFile of mdFiles) {
            const content = await fs.readFile(mdFile, 'utf-8')
            const matches = content.match(pattern_full)
            if (matches) {
                // console.log(`Found pattern in ${path.basename(mdFile)}:`, matches);

                // 下载每个匹配的URL
                for (const url of matches) {
                    await downloadImage(url)
                }

                const newContent = content.replace(pattern_sub, replacement)
                await fs.writeFile(mdFile, newContent, 'utf-8')
                console.log(`Substituted: ${path.basename(mdFile)}`)
                modifiedCount++
            }
        }
        console.log(`Modification count: ${modifiedCount}`)
    } catch (error) {
        console.error(`An exception occurred:`, error.message)
    }
}

if (import.meta.url === `file://${process.argv[1]}`) {
    substituteImageUrls()
}
