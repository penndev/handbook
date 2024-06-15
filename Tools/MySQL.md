- [主从配置](./Mysql.md#slave)

---


## 字符集

> 文本存储的字符集类型

- utf8mb4 常见兼容性强，常用。 

> 对字符进行排序的处理方式

- utf8mb4_bin 二进制排序
- utf8mb4_unicode_ci 不区分大小写排序等

## 索引

- `OPTIMIZE TABLE <tablename>` 优化表索引  清空被删除的记录，收回被浪费的空间，并重建表的索引等
- `EXPLAN <sql>` 分析SQL **分析的sql最好从慢日志里面取**
- [慢日志文档](https://mariadb.com/kb/en/slow-query-log-overview/)
 ```
 [mariadb] 
 ... 
 Slow_query_log
 // Slow_query_log_file=mariadb-slow.log
 log_output=FILE 
 long_query_time=5.0
 ```

## 事务

> 主要处理并发安全

```
[mariadb]
... 
transaction-isolation = REPEATABLE-READ


START TRANSACTION
COMMIT
ROLLBACK
```

**锁**
- 级别 表，行
- 类型 读锁（共享），写锁（独占，互斥，排他锁）


**隔离级别**

```
SELECT @@GLOBAL.transaction_isolation, @@transaction_isolation;
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
```

- `READ_UNCOMMITTED` **读未提交** *脏读：事务没有提交的数据也会被读取，如果回滚则会造成脏数据。*
- `READ-COMMITTED` **读已提交** *幻读 其他事务修改后，本次事务读取效果立即生效*
- `REPEATABLE-READ` **重复读** *幻读 事务开始后已读取数据将被缓存，再次读取效果一致，其他事务修改无效*
- `SERIALIZABLE` **串行化** *独占锁 并发性能低*


## 主从复制 {#slave}
> 前置条件 保证主从机器互通。从库业务账号最好使用只读账号。

1. 设置主库 
 - 修改配置`/etc/mysql/my.cnf`
    ```bash
    server-id=1
    log-bin=mysql-bin

    # 重启Mysql让配置生效
    ```

 - 锁定表并创建从库账户
    ```sql
    CREATE USER 'slave'@'%' IDENTIFIED BY '123456';
    GRANT REPLICATION SLAVE ON *.* TO 'slave'@'%';
    FLUSH PRIVILEGES;
    
    # 锁定所有表，以避免操作过程中数据未对齐
    FLUSH TABLES WITH READ LOCK;
    ```

 - 导出数据
     ```bash
     mysqldump -u root -p {database} > backup.sql
     ```

 - `SHOW MASTER STATUS;` 查看主库进度

2. 设置从库

 - 修改配置`/etc/mysql/my.cnf`
    ```bash
    server-id=2
    log-bin=mysql-bin
    
    # 重启Mysql让配置生效
    ```

  - 导入数据
    ```bash
    # 直接导入
    mysql -u root -p {database} < backup.sql
   
    # 登录后导入
    > use {database};
    > source backup.sql
    ```

  - 运行从库设置
    ```sql
    CHANGE MASTER TO
       MASTER_HOST='192.168.1.1',
       MASTER_USER='slave',
       MASTER_PASSWORD='123456',
       MASTER_LOG_FILE='mysql-bin.000001',
       MASTER_LOG_POS=1;
 
    # master 信息从 主库的最后一步确认
    ```

  - 查看从库状态
    ```sql
    SHOW SLAVE STATUS; #查看从库状态
    START SLAVE; #启动从库复制
    STOP SLAVE; #停止复制
    RESET SLAVE; #重置
    ```
