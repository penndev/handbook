
- [查看网络情况](./Network.md#show)

---

## 查看网络状态

```
ip addr
```

# 快速操作网卡命令

```
if up
if down
```

# 查看网络连接情况



```
netstat

netstat -an | grep ESTABLISHED | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr | head -n 10 查看建立连接最多的10个IP
```


# 统计流量

```
nload
```

# 配置网卡信息

验证网络管理工具
```
nmcli device status 
networkctl status 

ethtool eno1 #查看网卡信息

# 查看活跃的连接
nmcli connection show 
# 连接/断开某个网卡的配置
nmcli device disconnect eno1 &&  nmcli device connect enp131s0f0
nmcli device connect eno1
```
