
# 配置Prometheus监控

> grafana 做Prometheus 的监控面板


配置守护进程启动 `vim /usr/lib/systemd/system/prometheus.service`

```bash
[Unit]
Description=prometheus
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/prometheus/prometheus
WorkingDirectory=/usr/local/bin/prometheus

[Install]
WantedBy=multi-user.target


```