

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

## 内部location

`internal;` 关键字

X-Accel-Redirect


## openrestry 安装配置

> https://openresty.org/cn/linux-packages.html 官方预编译包


 

 ## 证书 ssl 配置

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