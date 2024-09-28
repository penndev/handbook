var md = require('markdown-it')(),
    mk = require('@vscode/markdown-it-katex').default;

md.use(mk);

// 读取文件内容
var fs = require('fs')
fs.readFile("Algo/README.md", 'utf8', (err, data) => {
if (err) {
    console.error('Error reading file:', err);
    return;
}

// 渲染 Markdown 文件内容
console.log(md.render(data));
});