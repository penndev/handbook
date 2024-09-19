
 ## 证书ssl配置

```
    #SSL
    ssl_certificate ssl/$ssl_server_name.crt;
    ssl_certificate_key ssl/$ssl_server_name.key;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    #SSL-END
```

## 缓存相关配置

```bash
# proxy_cache_path $cachedir levels=1:2 keys_zone=rootcache:100m max_size=10g 
# ----
# proxy_cache_path 配置缓存文件路径 
# levels=${前缀名称长度}:${前缀名称长度} 缓存文件路径层级
# keys_zone=${名称}:${初始内存} max_size=${最大限制} 配置缓存key配置内存大小和名称,
# inactive=${有效时间}
proxy_cache_path /tmp/ngcache levels=1:2 keys_zone=rootcache:100m;
```

## 反向代理

```
    proxy_pass $backend_url;
    proxy_set_header HOST $backend_host;

    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Client-Scheme $scheme;
    proxy_set_header X-Forward-For $remote_addr ;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header REMOTE-HOST $remote_addr;
```


## 静态文件服务器

- `alias` 静态文件路径，剔除location的文件路径。

- `root` 静态文件路径，未剔除location的文件路径。


## internal

> 当location包含 `internal;` 则表示本location只能nginx内部进行访问，如果通过uri访问则会返回404.

可通过 `error_page`、 `index`、 `internal_redirect`、 `random_index`和 `try_files`指令;和`rewrite`重定向、来自上游服务器的`X-Accel-Redirect`响应头字段重定向的请求。


## openrestry 

> https://openresty.org/cn/linux-packages.html 官方预编译包

