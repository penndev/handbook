# Kafka

生产者

broker -> 处理事件的节点

消费者


生产者向broker写入事件

事件：
    事件键：“爱丽丝”
    事件值：“向鲍勃支付 200 美元”
    事件时间戳：“2020年6月25日下午2:06”

消费者从broker读取事件


事件被持久存入`topic`中
topic像是文件夹，分区像是文件

[](./asset/kafka_topic.png)

图：此示例主题包含四个分区 P1–P4。两个不同的生产者客户端彼此独立地通过网络将事件写入主题的各个分区，从而向主题发布新事件。具有相同键（图中以颜色表示）的事件将被写入同一分区。请注意，如果适用，两个生产者都可以写入同一分区。

分区可以设置副本当存在三个节点，会保持数据始终可用。


## 安装 

docker run --name kafka  -p 9092:9092 -d apache/kafka:latest

docker run --name kafka-ui -p 38080:8080 --link kafka -e DYNAMIC_CONFIG_ENABLED=true -d provectuslabs/kafka-ui