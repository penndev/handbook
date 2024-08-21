- [清空宝塔登录日志](./bt.md#delsshlog)
- [调整自定义报警通知](./bt.md#webhooknotify)
---


## 清空宝塔登录日志 {#delsshlog}
> 服务器ssh攻击日志较多可用下面的脚本清理

```
echo > /var/log/auth.log
rm -rf /www/server/panel/data/ssh_cache.json
rm -rf /var/log/secure*
```

## 调整自定义报警通知 {#webhooknotify}

`/www/server/panel/class/msg/web_hook_msg.py:200`
> 将报错内容通过`GET` 中 $text 内容进行报错内容替换
```
        markdown_text = ""
        for key, value in real_data.items():
            value = value.strip().replace("<br>", "\n").replace("#", "")
            markdown_text += f"`{key.capitalize()}:`  {value}  \n"
        the_url = parse_url(the_url.url.replace("$text", markdown_text))
        ssl_verify=False
```