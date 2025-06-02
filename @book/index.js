var md = require("markdown-it")(),
  katex = require("@vscode/markdown-it-katex").default,
  attrs = require("markdown-it-attrs");

md.use(katex);
md.use(attrs);

module.exports = {
  hooks: {
    "page:before": function (page) {
      page.content =
        '<div class="markdown-it">' + md.render(page.content) + "</div>";
      return page;
    },
  },
};
