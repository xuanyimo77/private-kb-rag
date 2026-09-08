/**
 * Markdown 渲染工具：AI 答案以 markdown 返回，统一渲染为 HTML。
 */
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  linkify: true, // 自动识别链接
  breaks: true, // 换行转 <br>
  html: false, // 不渲染原始 HTML，防注入
})

export function renderMarkdown(text: string): string {
  return md.render(text || '')
}
