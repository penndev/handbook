## ubuntu设置root远程登录

1. 首先设置root密码

2. 开启root登录 `/etc/ssh/sshd_config`设置位`PermitRootLogin yes`

3. 重启ssh服务 `sudo service ssh restart`
