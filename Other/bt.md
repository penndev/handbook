# 宝塔使用技巧


** 清空宝塔登录日志 **
```
echo > /var/log/auth.log
rm -rf /www/server/panel/data/ssh_cache.json
rm -rf /var/log/secure*
```


** 调整自定义报警通知 webhook**

`/www/server/panel/class/msg/web_hook_msg.py:200`
> 将报错内容通过`GET` 中 $text 内容进行报错内容替换
```
        markdown_text = ""
        for key, value in real_data.items():
            markdown_text += f"`{key.capitalize()}:`  {value}  \n"
        the_url = parse_url(the_url.url.replace("$text", markdown_text.strip().replace("<br>", "\n").replace("#", "")))
```