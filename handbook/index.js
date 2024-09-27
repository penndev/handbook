const katex = require('katex');

module.exports = {
    book: {
        assets: "./_assets",
        css: ["katex.min.css", "main.css"]
    },
    hooks: {
        // 配置钩子
        // "config": function(config) {
        //     config.styles = config.styles || config.pluginsConfig["handbook"].styles || [];
        //     config.styles.push('../node_modules/katex/dist/katex.min.css');
        //     return config;
        // },
        "page:before": function(page) {
            page.content = page.content.replace(/(\$)(\r?\n)/g, "$1 $2");
            return page;
            
        },
        "page": function(page) {
            let content = page.content;
            content = content.replace(/\$([^\$]+?)\$\s/g, (match, p1) => {
                try {return katex.renderToString(p1);
                } catch (error) {
                    console.error(error);
                    return match;
                }
            });
            content = content.replace(/\$\$([^\$]+?)\$\$\s/g, (match, p1) => {
                try {return katex.renderToString(p1);
                } catch (error) {
                    console.error(error);
                    return match;
                }
            });

            page.content = content;
            return page;
        }
    }
};
