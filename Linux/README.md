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

# TCP参数调优
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_syncookies = 1 
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_max_syn_backlog = 16384

# 防止连接被丢弃 常用连接队列参数
net.netfilter.nf_conntrack_max = 524288 
net.netfilter.nf_conntrack_tcp_timeout_max_retrans  = 30
net.core.somaxconn = 16384
net.core.netdev_max_backlog = 5000




```

## 安全设置

fail2ban 防爆破工具