var md = require('markdown-it')(),
    mk = require('@vscode/markdown-it-katex').default;

md.use(mk);

module.exports = {
    book: {
        assets: "./_assets",
        css: ["katex.min.css", "main.css"]
    },
    hooks: {
        "page:before": function(page) {
            page.content = '<div class="markdown-it">' + md.render(page.content) + '</div>'
            return page;
        },
    }
};
