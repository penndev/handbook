# IP 地址库

IP 地域识别在业务里越来越常见，常见场景包括：

- **商业区域化**：按地区做内容、活动、合规分流
- **安全风控**：识别危险 IP、代理/VPN、异常访问
- **地域封禁与准入**：按国家/省市做策略控制

数据格式虽多，核心需求始终是：**可定期更新的 IP → 地域映射**。业界常用两家维护方：

| 厂商 | 侧重 | 社区版 | 优点
|------|------|--------|
| [纯真网络](https://www.cz88.net/) | 国内 IP 更准、更新更勤 | 有（注意授权） | 境内详细准确
| [MaxMind](https://www.maxmind.com/) | 海外覆盖更全 | 有（注意授权） | 全球化

## 纯真（CZ88）

官网：[https://www.cz88.net/](https://www.cz88.net/)

### 格式演进

| 格式 | 状态 | 说明 | 项目地址
|------|------|------|
| `qqwry.dat` | 已停更 | 官方 2024 年 10 月起不再维护，也不再发布 dat |  (https://github.com/penndev/gopkg/tree/main/qqwry)
| `czdb` | 现行 | 新格式；含 IPv4 / IPv6；源数据能力仍延续纯真体系 |  https://github.com/penndev/gopkg/tree/main/ip2region

源数据czdb在qqwry的基础上进行了部分的授权收紧(技术上的)，官方库需要解密,根据官方库想让塔保证简单。所以按照下面的流程可以用ip2region的数据库，但是数据源仍然是czdb。


 
| 解析旧版 `qqwry.dat` | [gopkg/qqwry] |
| 拆解 `czdb` → geoip 文本 | [gopkg/test/czdb](https://github.com/penndev/gopkg/tree/main/test/czdb) |
| 封装为 `xdb` | [ip2region/maker](https://github.com/lionsoul2014/ip2region/tree/master/maker) |
| 生成 `xdb` 示例 | [example/czdb/main.go](https://github.com/penndev/gopkg/blob/main/example/czdb/main.go) | 

> **数据包要点**：`czdb` 使用 B-tree 索引，且含加密段，不能当普通明文 IP 表直接读。

### 推荐自建路径

把官方 `czdb` 转成 `xdb`，再接入业务查询：

1. 用上述 `czdb` 拆解脚本，导出 geoip 列表（txt）
2. 用 ip2region 的 maker 打成 `xdb`
3. **请自行用自己的授权包重新生成**，不要直接传播他人的官方下载包

授权对照：

- `xdb` / ip2region：**Apache-2.0**
- 纯真社区版：须遵守官方条款（见下）

### 纯真社区版授权要点


