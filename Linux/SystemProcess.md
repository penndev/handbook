- [查看概况](./SystemProcess.md#show)
- 守护进程
  - [systemd](./SystemProcess.md#systemd)
  - [supervisor](./SystemProcess.md#supervisor)
---

## 概况查看 {#show}

**进程运行时**

`/proc/{pid}`

- 查看进程的执行文件
  ```bash
  ls -al /proc/{pid}/exe
  ```


**发送信号到进程**

```
 kill 9 1000 1001 1002
 pkill nginx
```


## 守护进程

### systemd {#systemd}

`vim /usr/lib/systemd/system/wafcdn.service` 配置文件

```bash
[Unit]
Description=WafCdn Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/wafcdn/wafcdn
WorkingDirectory=/usr/local/wafcdn/wafcdn

[Install]
WantedBy=multi-user.target

```

- `systemctl disable|enable|status|start|stop|restart wafcdn`

### Supervisor {#supervisor}

**安装Supervisor**

_`/tmp`文件会在空闲时间被清理_

_系统open file limit 设置_

1. 安装 `pip install supervisor`
2. 生成配置文件 `echo_supervisord_conf > /etc/supervisord.conf`
3. 添加supervisor到守护进程 `vim /usr/lib/systemd/system/supervisord.service`
  ```bash
  #supervisord.service

  [Unit] 
  Description=Supervisor daemon

  [Service] 
  Type=forking 
  ExecStart=/usr/local/bin/supervisord -c /etc/supervisord.conf
  ExecStop=/usr/local/bin/supervisorctl shutdown 
  ExecReload=/usr/local/bin/supervisorctl reload 
  KillMode=process 
  Restart=on-failure 
  RestartSec=42s

  [Install] 
  WantedBy=multi-user.target
  ```
4. 设置守护进程启动
  ```bash
  systemctl enable supervisord
  systemctl start supervisord
  systemctl status supervisord
  ```
5. 确定supervisor配置文件 `/etc/supervisord.conf` 
```bash
[include] 
files = /etc/supervisord.d/*.ini
```


**配置supervisor启动程序**

  `vim /etc/supervisord.d/cdnload.ini`

  ```bash
  [program:cdn]
  command=/www/wwwroot/cdnload
  directory=/www/wwwroot
  autorestart=true
  stdout_logfile=/www/wwwlogs/cdnload.out.log
  stderr_logfile=/www/wwwlogs/cdnload.err.log
  user=root
  ```

  

 **管理supervisor**
 
 ```bash
 supervisorctl status|update|reload
 ```
 
 **管理supervisor进程**
 
 ```bash
 supervisorctl start|stop|restart|clear {program:name}
 ```

