# 宝塔使用技巧


## 常用安全配置

密码防爆破

- 安装ssh防护fail2ban工具
- 修改ssh默认端口不为`22`
- 修改某些版本的宝塔8888默认端口
- 安全中关闭不用的端口

IP地址白名单






** 调整自定义报警通知 webhook**

`/www/server/panel/class/msg/web_hook_msg.py:200`

```
        markdown_text = ""
        for key, value in real_data.items():
            markdown_text += f"`{key.capitalize()}:`  {value}  \n"
        the_url = parse_url(the_url.url.replace("$text", markdown_text))
```