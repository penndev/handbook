# Linux

> https://www.kernel.org/


## 文件限制
```
vim /etc/security/limits.conf

* hard nofile 102400
* soft nofile 102400

# 需要重启进程后生效
```

## 网络优化
```
vim /etc/sysctl.conf
sysctl -p

# 重用回收 time_wait 连接
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 1

net.ipv4.tcp_syncookies = 1 
net.ipv4.tcp_fin_timeout = 30
# 防止连接被丢弃
net.netfilter.nf_conntrack_max = 262144 
```
