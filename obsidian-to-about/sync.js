#!/usr/bin/env node
/**
 * Obsidian 到 About 同步脚本
 * 将 Obsidian 收藏夹同步到 about 项目
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
      // 解析数组格式 [item1, item2]
      if (value.startsWith('[') && value.endsWith(']')) {
        try {
          value = JSON.parse(value.replace(/'/g, '"'));
        } catch {
          value = value.slice(1, -1).split(',').map(v => v.trim());
        }
      }
      // 去除引号
      if (typeof value === 'string' && value.startsWith('"') && value.endsWith('"')) {
        value = value.slice(1, -1);
      }
      frontmatter[key] = value;
    }
  });

  return { frontmatter, body };
}

/**
 * 转换收藏夹格式
 */
function convertBookmark(content, filename) {
  const { frontmatter, body } = parseFrontmatter(content);

  // 提取日期从文件名
  const dateMatch = filename.match(/^(\d{4}-\d{2}-\d{2})/);
  const fileDate = dateMatch ? dateMatch[1] : new Date().toISOString().split('T')[0];

  // 构建新的 frontmatter
  const title = frontmatter.title || '';
  const authors = Array.isArray(frontmatter.authors) ? frontmatter.authors.join(', ') : (frontmatter.authors || '');
  const source = frontmatter.source || '';
  const url = frontmatter.url || '';
  const date = frontmatter.date || fileDate;
  const tags = Array.isArray(frontmatter.tags) ? frontmatter.tags : [];
  const tagsStr = tags.map(t => `#${t}`).join(' ');

  // 转换正文：移除 "原文 | 来源 | 日期" 的引用行
  let convertedBody = body
    .replace(/^> \*\*原文\*\* \| .*$/gm, '')
    .replace(/^> \*\*作者\*\*:.*$/gm, '')
    .replace(/^> 研究机构:.*$/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  // 构建输出
  const output = `---
标题: ${title}
作者: ${authors}
来源: ${url || source}
日期: ${date}
标签: ${tagsStr}
---

${convertedBody}
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
 * 主同步函数
 */
async function sync() {
  console.log('🔄 开始同步 Obsidian 收藏夹到 about 项目...\n');

  // 检查目录是否存在
  if (!fs.existsSync(OBSIDIAN_BOOKMARKS_DIR)) {
    console.error(`❌ Obsidian 收藏夹目录不存在: ${OBSIDIAN_BOOKMARKS_DIR}`);
    process.exit(1);
  }

  if (!fs.existsSync(ABOUT_BOOKMARKS_DIR)) {
    console.error(`❌ About 收藏夹目录不存在: ${ABOUT_BOOKMARKS_DIR}`);
    process.exit(1);
  }

  // 获取文件列表
  const obsidianFiles = getMarkdownFiles(OBSIDIAN_BOOKMARKS_DIR);
  const aboutFiles = getMarkdownFiles(ABOUT_BOOKMARKS_DIR);

  console.log(`📁 Obsidian 收藏夹: ${obsidianFiles.length} 个文件`);
  console.log(`📁 About 收藏夹: ${aboutFiles.length} 个文件`);

  // 找出需要同步的文件（Obsidian 中有但 about 中没有的）
  const filesToSync = obsidianFiles.filter(f => !aboutFiles.includes(f));

  if (filesToSync.length === 0) {
    console.log('\n✅ 没有新文件需要同步');
    return;
  }

  console.log(`\n📤 需要同步 ${filesToSync.length} 个新文件:`);
  filesToSync.forEach(f => console.log(`   - ${f}`));

  // 同步文件
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

  // Git 操作
  if (successCount > 0) {
    console.log('\n📝 执行 Git 提交...');

    // 检查是否有变更
    const statusResult = execCommand('git status --porcelain', ABOUT_GIT_DIR);
    if (!statusResult.success || !statusResult.output) {
      console.log('   ℹ️ 没有需要提交的变更');
      return;
    }

    // 添加文件
    const addResult = execCommand('git add content/bookmarks/', ABOUT_GIT_DIR);
    if (!addResult.success) {
      console.error(`   ❌ Git add 失败: ${addResult.error}`);
      return;
    }

    // 提交
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    const timeStr = now.toTimeString().slice(0, 5);
    const commitMsg = `sync(obsidian): 同步收藏夹 - ${dateStr} ${timeStr}`;

    const commitResult = execCommand(`git commit -m "${commitMsg}"`, ABOUT_GIT_DIR);
    if (!commitResult.success) {
      console.error(`   ❌ Git commit 失败: ${commitResult.error}`);
      return;
    }
    console.log(`   ✅ 已提交: ${commitMsg}`);

    // 先拉取远程更新
    console.log('   📥 拉取远程更新...');
    const pullResult = execCommand('git pull --rebase', ABOUT_GIT_DIR);
    if (!pullResult.success) {
      console.error(`   ❌ Git pull 失败: ${pullResult.error}`);
      // 尝试中止 rebase 并恢复
      execCommand('git rebase --abort', ABOUT_GIT_DIR);
      return;
    }
    console.log('   ✅ 已同步远程更新');

    // 推送
    const pushResult = execCommand('git push', ABOUT_GIT_DIR);
    if (!pushResult.success) {
      console.error(`   ❌ Git push 失败: ${pushResult.error}`);
      return;
    }
    console.log('   ✅ 已推送到远程仓库');
  }

  console.log('\n🎉 同步完成!');
}

// 运行同步
sync().catch(error => {
  console.error('❌ 同步失败:', error);
  process.exit(1);
});
