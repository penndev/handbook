

## 索引

- `OPTIMIZE TABLE <tablename>` 优化表索引  清空被删除的记录，收回被浪费的空间，并重建表的索引等
- `EXPLAN <sql>` 分析SQL **分析的sql最好从慢日志里面取**


## 主从复制
> 前置条件 保证主从机器互通。从库业务账号最好使用只读账号。

1. 设置主库 
 - 修改配置`/etc/mysql/my.cnf`

    ```bash
    server-id=1
    log-bin=mysql-bin
    ```

 - 锁定表并创建从库账户

    ```sql
    CREATE USER 'slave'@'%' IDENTIFIED BY '123456';
    GRANT REPLICATION SLAVE ON *.* TO 'slave'@'%';
    FLUSH PRIVILEGES;

    FLUSH TABLES WITH READ LOCK;
    SHOW MASTER STATUS;
    ```

 - `mysqldump` 导出数据

 - `SHOW MASTER STATUS;` 查看主库进度

2. 设置从库

 - 修改配置`/etc/mysql/my.cnf`

    ```bash
    server-id=2
    log-bin=mysql-bin
    ```

- 导入 `mysqldump` 文件

- 运行从库设置

    ```sql
    CHANGE MASTER TO
        MASTER_HOST='192.168.1.1',
        MASTER_USER='slave',
        MASTER_PASSWORD='123456',
        MASTER_LOG_FILE='mysql-bin.000001',
        MASTER_LOG_POS=1;
    ```

- 查看从库状态

    ```sql
    SHOW SLAVE STATUS; #查看从库状态
    START SLAVE; #启动从库复制
    STOP SLAVE; #停止复制
    RESET SLAVE; #重置
    ```
