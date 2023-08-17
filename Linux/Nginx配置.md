

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


## openrestry 安装配置

> https://openresty.org/cn/linux-packages.html 官方预编译包
