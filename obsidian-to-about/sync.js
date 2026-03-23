#!/usr/bin/env node
/**
 * Obsidian 到 About 同步脚本
 * 遵循 BOOKMARK_RULES.md 规范进行同步和格式转换
 */

const fs = require('fs');
const path = require('path');

// 配置路径
const OBSIDIAN_BOOKMARKS_DIR = '/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Resources/收藏夹';
const ABOUT_BOOKMARKS_DIR = '/Users/xuandao/.openclaw/workspace/git/about/content/bookmarks';
const ABOUT_GIT_DIR = '/Users/xuandao/.openclaw/workspace/git/about';

/**
 * 解析 frontmatter
 */
function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n/);
  if (!match) return { frontmatter: {}, body: content };

  const frontmatterText = match[1];
  const body = content.slice(match[0].length);

  const frontmatter = {};
  frontmatterText.split('\n').forEach(line => {
    const colonIndex = line.indexOf(':');
    if (colonIndex > 0) {
      const key = line.slice(0, colonIndex).trim();
      let value = line.slice(colonIndex + 1).trim();
      
      // 解析数组格式 [item1, item2] 或 - item1
      if (value.startsWith('[') && value.endsWith(']')) {
        try {
          value = JSON.parse(value.replace(/'/g, '"'));
        } catch {
          value = value.slice(1, -1).split(',').map(v => v.trim().replace(/^['"](.*)['"]$/, '$1'));
        }
      } else if (typeof value === 'string' && value.startsWith('"') && value.endsWith('"')) {
        value = value.slice(1, -1);
      }
      
      frontmatter[key] = value;
    }
  });

  return { frontmatter, body };
}

/**
 * 转换收藏夹格式 (遵循 BOOKMARK_RULES.md)
 */
function convertBookmark(content, filename) {
  const { frontmatter, body } = parseFrontmatter(content);

  // 1. 提取日期
  const dateMatch = filename.match(/^(\d{4}-\d{2}-\d{2})/);
  const fileDate = dateMatch ? dateMatch[1] : new Date().toISOString().split('T')[0];
  const date = frontmatter.date || fileDate;

  // 2. 提取标题
  let title = frontmatter.title || frontmatter.标题 || '';
  if (!title) {
    const titleMatch = body.match(/^# (.*)/m);
    title = titleMatch ? titleMatch[1].trim() : filename.replace(/^\d{4}-\d{2}-\d{2}-/, '').replace(/\.md$/, '');
  }

  // 3. 提取链接
  const url = frontmatter.url || frontmatter.source || frontmatter.来源 || '';

  // 4. 提取标签 (确保是数组)
  let tags = frontmatter.tags || frontmatter.标签 || [];
  if (typeof tags === 'string') {
    tags = tags.split(/[\s,，]+/).map(t => t.replace(/^#/, '')).filter(t => t);
  } else if (!Array.isArray(tags)) {
    tags = [];
  }

  // 5. 提取描述
  const description = frontmatter.description || frontmatter.描述 || '';

  // 6. 提取摘要 (优先从 frontmatter 提取，若无则从正文提取)
  let summary = frontmatter.summary || frontmatter.摘要 || '';
  if (!summary) {
    // 尝试匹配 ## 摘要 之后的内容
    const summaryHeaderMatch = body.match(/## 摘要\n+([\s\S]*?)(?=\n\n#|\n\n##|\n---|$)/);
    if (summaryHeaderMatch) {
      summary = summaryHeaderMatch[1].trim();
    } else {
      // 尝试匹配引用块格式的摘要
      const summaryQuoteMatch = body.match(/^> 摘要\n> ([\s\S]*?)(?=\n\n|$)/m);
      if (summaryQuoteMatch) {
        summary = summaryQuoteMatch[1].replace(/^> /gm, '').trim();
      }
    }
  }
  
  // 清理摘要中的 Markdown 标记 (去除引用符号、换行符和尾随的分隔符)
  if (summary) {
    summary = summary
      .replace(/^> /gm, '')              // 移除每行开头的引用符号
      .replace(/---/g, '')               // 移除分隔符
      .replace(/[\n\r]+/g, ' ')         // 换行替换为空格
      .replace(/\s+/g, ' ')             // 多个空格合并
      .trim();
    if (summary.length > 300) summary = summary.slice(0, 297) + '...';
  } else {
    // 最后退而求其次取正文前 200 字
    summary = body.replace(/^# .*\n/g, '').trim().slice(0, 200).replace(/[\n\r]+/g, ' ') + '...';
  }

  // 7. 正文处理 (确保有 # 标题)
  let finalBody = body.trim();
  if (!finalBody.startsWith('# ')) {
    finalBody = `# ${title}\n\n${finalBody}`;
  }

  // 构建输出 (标准格式)
  const output = `---
title: ${JSON.stringify(title)}
url: ${JSON.stringify(url)}
date: ${JSON.stringify(String(date))}
tags: ${JSON.stringify(tags)}
description: ${JSON.stringify(description)}
summary: ${JSON.stringify(summary)}
---

${finalBody}
`;

  return output;
}

/**
 * 获取目录中的 .md 文件列表
 */
function getMarkdownFiles(dir) {
  if (!fs.existsSync(dir)) {
    console.log(`目录不存在: ${dir}`);
    return [];
  }
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.md'))
    .sort();
}

/**
 * 执行 shell 命令
 */
function execCommand(command, cwd) {
  const { execSync } = require('child_process');
  try {
    const result = execSync(command, { cwd, encoding: 'utf-8' });
    return { success: true, output: result.trim() };
  } catch (error) {
    return { success: false, error: error.message, output: error.stdout?.trim() || '' };
  }
}

/**
 * 验证并修复现有文件
 */
async function validateAndFixAll() {
  console.log('🔍 开始验证并修复现有收藏夹文章...\n');

  if (!fs.existsSync(ABOUT_BOOKMARKS_DIR)) {
    console.error(`❌ About 收藏夹目录不存在: ${ABOUT_BOOKMARKS_DIR}`);
    return;
  }

  const aboutFiles = getMarkdownFiles(ABOUT_BOOKMARKS_DIR);
  let fixCount = 0;

  for (const filename of aboutFiles) {
    const filePath = path.join(ABOUT_BOOKMARKS_DIR, filename);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 检查是否符合规范 (简单检查关键字段是否存在且为英文)
    const { frontmatter } = parseFrontmatter(content);
    const isCompliant = frontmatter.title !== undefined && 
                        frontmatter.url !== undefined && 
                        frontmatter.date !== undefined && 
                        frontmatter.summary !== undefined;

    if (!isCompliant || frontmatter.标题 || frontmatter.来源 || frontmatter.标签 || frontmatter.摘要) {
      console.log(`   🛠️  修复文件: ${filename}`);
      try {
        const fixedContent = convertBookmark(content, filename);
        fs.writeFileSync(filePath, fixedContent, 'utf-8');
        fixCount++;
      } catch (error) {
        console.error(`   ❌ 修复失败: ${filename} - ${error.message}`);
      }
    }
  }

  console.log(`\n📊 验证完成: 共处理 ${aboutFiles.length} 个文件，修复了 ${fixCount} 个文件。`);
  return fixCount;
}

/**
 * 主同步函数
 */
async function sync() {
  const args = process.argv.slice(2);
  const isFixMode = args.includes('--fix');

  if (isFixMode) {
    const fixed = await validateAndFixAll();
    if (fixed > 0) {
      console.log('\n📝 执行 Git 提交修复内容...');
      const statusResult = execCommand('git status --porcelain', ABOUT_GIT_DIR);
      if (statusResult.success && statusResult.output) {
        execCommand('git add content/bookmarks/', ABOUT_GIT_DIR);
        const commitMsg = `chore(bookmarks): 修复现有文章格式以符合 BOOKMARK_RULES.md`;
        execCommand(`git commit -m "${commitMsg}"`, ABOUT_GIT_DIR);
        execCommand('git pull --rebase', ABOUT_GIT_DIR);
        execCommand('git push', ABOUT_GIT_DIR);
        console.log('   ✅ 修复已同步到远程仓库');
      }
    }
    return;
  }

  console.log('🔄 开始同步 Obsidian 收藏夹 (遵循 BOOKMARK_RULES.md)...\n');

  if (!fs.existsSync(OBSIDIAN_BOOKMARKS_DIR)) {
    console.error(`❌ Obsidian 收藏夹目录不存在: ${OBSIDIAN_BOOKMARKS_DIR}`);
    process.exit(1);
  }

  if (!fs.existsSync(ABOUT_BOOKMARKS_DIR)) {
    console.error(`❌ About 收藏夹目录不存在: ${ABOUT_BOOKMARKS_DIR}`);
    process.exit(1);
  }

  const obsidianFiles = getMarkdownFiles(OBSIDIAN_BOOKMARKS_DIR);
  const aboutFiles = getMarkdownFiles(ABOUT_BOOKMARKS_DIR);

  console.log(`📁 Obsidian 收藏夹: ${obsidianFiles.length} 个文件`);
  console.log(`📁 About 收藏夹: ${aboutFiles.length} 个文件`);

  // 找出需要同步的文件
  const filesToSync = obsidianFiles.filter(f => !aboutFiles.includes(f));

  if (filesToSync.length === 0) {
    console.log('\n✅ 没有新文件需要同步');
    return;
  }

  console.log(`\n📤 需要同步 ${filesToSync.length} 个新文件:`);

  let successCount = 0;
  for (const filename of filesToSync) {
    try {
      const sourcePath = path.join(OBSIDIAN_BOOKMARKS_DIR, filename);
      const targetPath = path.join(ABOUT_BOOKMARKS_DIR, filename);

      const content = fs.readFileSync(sourcePath, 'utf-8');
      const convertedContent = convertBookmark(content, filename);

      fs.writeFileSync(targetPath, convertedContent, 'utf-8');
      console.log(`   ✅ 已同步: ${filename}`);
      successCount++;
    } catch (error) {
      console.error(`   ❌ 同步失败: ${filename} - ${error.message}`);
    }
  }

  console.log(`\n📊 同步完成: ${successCount}/${filesToSync.length} 个文件`);

  if (successCount > 0) {
    console.log('\n📝 执行 Git 提交...');

    const statusResult = execCommand('git status --porcelain', ABOUT_GIT_DIR);
    if (!statusResult.success || !statusResult.output) {
      console.log('   ℹ️ 没有需要提交的变更');
      return;
    }

    execCommand('git add content/bookmarks/', ABOUT_GIT_DIR);
    
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    const timeStr = now.toTimeString().slice(0, 5);
    const commitMsg = `sync(obsidian): 同步收藏夹 - ${dateStr} ${timeStr}`;

    const commitResult = execCommand(`git commit -m "${commitMsg}"`, ABOUT_GIT_DIR);
    if (commitResult.success) {
      console.log(`   ✅ 已提交: ${commitMsg}`);
      
      console.log('   📥 同步远程仓库...');
      execCommand('git pull --rebase', ABOUT_GIT_DIR);
      const pushResult = execCommand('git push', ABOUT_GIT_DIR);
      if (pushResult.success) {
        console.log('   ✅ 已推送到远程仓库');
      }
    }
  }

  console.log('\n🎉 所有任务已完成!');
}

sync().catch(error => {
  console.error('❌ 同步过程中发生错误:', error);
  process.exit(1);
});
