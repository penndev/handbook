# Kafka
> kafka 是一个生产消费队列 可以对数据持久化 支持横向拓展 速度极快


## 角色

- 生产者 Producer

- 消费者 Consumer

- 服务者 broker

- 控制器 Controller

- 集群


![](./asset/kafka_topic.png)

图：此示例主题包含四个分区 P1–P4。两个不同的生产者客户端彼此独立地通过网络将事件写入主题的各个分区，从而向主题发布新事件。具有相同键（图中以颜色表示）的事件将被写入同一分区。请注意，如果适用，两个生产者都可以写入同一分区。

分区可以设置副本当存在三个节点，会保持数据始终可用。



## 安装 

docker run --name kafka -p 9092:9092 -d apache/kafka:latest


ui
```bash
java  kafka-ui-api-v0.7.2.jar --spring.config.additional-location=config.yaml

> config.yaml
kafka:
  clusters:
    - name: local
      bootstrapServers: "localhost:9092"
```