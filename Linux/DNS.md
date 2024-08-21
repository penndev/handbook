## DNS数据包封装接口

### Header section format
```
https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.1
 0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      ID                       |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE   |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    QDCOUNT                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    ANCOUNT                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    NSCOUNT                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    ARCOUNT                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```
- ID[16b]  查询ID或者响应ID
- QR[1b]   
    - 0 表示是查询请求
    - 1 标识是返回数据
- Opcode[4b]
    - 0 (QUERY): 标准查询，这是最常见的操作类型，用于执行基本的域名解析。
    - 1 (IQUERY): 反向查询（已废弃，不再使用）。
    - 2 (STATUS): 服务器状态请求（也很少使用）。
    - 3-15保留
- AA[1b] 是否权威应答 
    - 0 表示可以从缓存去数据， 
    - 1表示是权威服务器返回数据。
- TC[1b] 传输截断标志位
- RD[1b] 是否递归查询
- RA[1b] 是否支持递归
- Z[3b] 保留位
- RCODE[4b]
    - 0 无错误条件
    - 1 格式错误,名称服务器无法解释查询。
    - 2 服务器故障,由于名称服务器出现问题，名称服务器无法处理此查询。
    - 3 名称错误,此代码仅对权威名称服务器的响应有意义，表示查询中引用的域名不存在。
    - 4 未实现,名称服务器不支持所请求的查询类型。
    - 5 拒绝,名称服务器出于策略原因拒绝执行指定操作。例如，名称服务器可能不希望向特定请求者提供信息，或者名称服务器可能不希望对特定数据执行特定操作（例如区域传输）。
    - 6-15 保留以备将来使用。
- QDCOUNT[16b] 查询记录数
- ANCOUNT[16b] 应答记录数
- NSCOUNT[16b] NS记录数
- ARCOUNT[16b] 额外记录数


### Question section format
```
https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.2

 0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                                               |
/                     QNAME                     /
/                                               /
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                     QTYPE                     |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                     QCLASS                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

```
- QNAME： 变长 字节长度 + 字符数据 如果下字节为0则结束否则要循环
- QTYPE类型：https://datatracker.ietf.org/doc/html/rfc1035#section-3.2.2
- QCLASS类型：https://datatracker.ietf.org/doc/html/rfc1035#section-3.2.4


**请求封装示例：** 

```
184, 105, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 7, 97, 108, 105, 98, 97, 98, 97, 3, 99, 111, 109, 0, 0, 1, 0, 1

- 头部分(固定12位，参考文档说明): 184, 105, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0
- 域名部分: (变长[字符长度，字符数据])
    - 7, 97, 108, 105, 98, 97, 98, 97, 
    - 3, 99, 111, 109, 
    - 0， 结束标志位 
- QTYPE（查询类型）： 0, 1, 
- QCLASS：(网络类型) 0, 1, 0, 1,
```

### Resource record format

```
https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.3
  0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                                               |
/                                               /
/                      NAME                     /
|                                               |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      TYPE                     |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                     CLASS                     |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      TTL                      |
|                                               |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                   RDLENGTH                    |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|
/                     RDATA                     /
/                                               /
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```
- 前字段与请求段类似
- TTLI(32b):  dns的生存周期返回数据的长度
- RDLENGTH (16b): RDATA的长度。
- RDATA (RDLENGTH byte): 实际数据， RDATA与NAME 可能会有数据压缩。

**详细的实现步骤请参考 [Dart(flutter) 代码](./DNS.dart)**





## Doh(Dns over https)
> 通过https进行dns查询  rfc文件格式是https://datatracker.ietf.org/doc/html/rfc8484

### GET

```bash
    :method = GET
    :scheme = https
    :authority = dnsserver.example.net
    :path = /dns-query?dns=AAABAAABAAAAAAAAA3d3dwdleGFtcGxlA2NvbQAAAQAB
    accept = application/dns-message
```
- dns 中的参数使用 base64url 原始的dns二进制message

### POST

```bash
:method = POST
:scheme = https
:authority = dnsserver.example.net
:path = /dns-query
accept = application/dns-message
content-type = application/dns-message
content-length = 33
<33 bytes represented by the following hex encoding>
00 00 01 00 00 01 00 00  00 00 00 00 03 77 77 77
07 65 78 61 6d 70 6c 65  03 63 6f 6d 00 00 01 00
01
```
