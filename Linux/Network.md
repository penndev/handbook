
- [查看网络情况](./Network.md#show)

---

## 查看网络状态

```
ip addr
```

# 快速操作网卡命令

if up
if down

# 查看网络连接情况

netstat 

`netstat -an | grep ESTABLISHED | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr | head -n 10` 查看建立连接最多的10个IP

# 统计流量

nload