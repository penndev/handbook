# elasticsearch


```bash
docker run -d --name elasticsearch --network dev --restart always -p 9200:9200 \
-e discovery.type=single-node  \
-e ELASTIC_PASSWORD=123456  \
-e xpack.security.enabled=true  \
-e xpack.security.http.ssl.enabled=false  \
-e xpack.security.transport.ssl.enabled=false  \
-e ES_JAVA_OPTS="-Xms1g -Xmx1g"  \
elasticsearch:9.2.0

# 设置kibana_system用户密码，供kibana使用
elasticsearch-reset-password -u kibana_system -i
> 123456
```

> 容器环境必须配置elasticsearch用户才能启动kibana

```bash
docker run -d --name kibana --network dev --restart always -p 5601:5601 \
-e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
-e ELASTICSEARCH_USERNAME=kibana_system \
-e ELASTICSEARCH_PASSWORD=123456 \
kibana:9.2.0
```

## 使用示例