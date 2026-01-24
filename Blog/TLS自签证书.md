# HTTPS证书

tls,https证书都是 X.509 的格式标准 pem cer crt der p12都是证书的封装格式。

## 生成根证书

- 生成证书配置文件 `ssl.conf`
    ```bash
    [ req ]                                  # req 模块配置入口
    default_bits       = 4096                # 默认生成 RSA 私钥长度，根 CA 建议 4096
    distinguished_name = req_distinguished_name # 指定证书主体信息段名
    x509_extensions    = v3_ca               # 生成自签证书时使用的 X.509 v3 扩展段
    prompt             = no                  # 禁用交互式输入，全部使用配置文件

    [ req_distinguished_name ]               # 证书主体信息（Subject DN）
    C  = CN                                  # 国家代码（Country）
    ST = ShangHai                             # 省 / 州（State / Province）
    L  = ShangHai                             # 城市（Locality）
    O  = github.com/penndev                   # 组织名称（Organization）
    OU = PennDev                             # 组织单位（Organizational Unit）
    CN = PenndevRoot                         # 通用名，根证书名称（不是域名）

    [ v3_ca ]                                # X.509 v3 扩展（CA 专用）
    basicConstraints = critical, CA:TRUE     # 标记为 CA 证书，critical 表示必须识别
    keyUsage = critical, keyCertSign, cRLSign
                                            # keyCertSign：允许签发证书
                                            # cRLSign：允许签发吊销列表
                                            # critical：客户端必须支持该扩展
    subjectKeyIdentifier = hash              # 根据公钥生成主体密钥标识（SKI）
    authorityKeyIdentifier = keyid:always    # 生成授权密钥标识（AKI），指向自身
    ```
- 生成公私钥
  `openssl req x509 -nodes -days 3650  -keyout rootCA.key -out rootCA.crt -config ssl.conf`



## 签署某个域名

1. 创建服务端私钥 
  `openssl genrsa -out example.com.key 2048` 
2. 生成服务端公钥，并申请认证签名表格CSR 认证信息如下`server.conf` 
    ```bash
    [ req ]                                  # req 主配置
    default_bits       = 2048                # 服务器证书 2048 即可
    distinguished_name = req_distinguished_name # Subject DN
    req_extensions     = v3_req              # CSR 使用的扩展
    prompt             = no                  # 禁用交互

    [ req_distinguished_name ]               # 服务器主体信息
    C  = CN                                  # 国家
    ST = ShangHai                             # 省 / 州
    L  = ShangHai                             # 城市
    O  = MyCompany                           # 公司名
    OU = IT                                 # 部门
    CN = example.com                         # 主域名（仅展示）

    [ v3_req ]                               # 服务器证书扩展
    basicConstraints = CA:FALSE              # 明确不是 CA
    keyUsage = critical, digitalSignature, keyEncipherment
                                            # TLS 握手必需用途
    extendedKeyUsage = serverAuth            # 标记为服务器证书
    subjectAltName = @alt_names              # SAN 配置入口

    [ alt_names ]                            # SAN 列表（核心）
    DNS.1 = example.com                      # 主域名
    DNS.2 = www.example.com                  # 备用域名
    ``` 
    `openssl req -new -key example.com.key -out example.com.csr  -config server.conf`

3. 根据 中间证书,根证书，来生成公钥 公钥部分因为自签所以 server.conf 申请都同意，所以直接复用 server.conf文件
    ```sh
    openssl x509 -req -in example.com.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out example.com.crt -days 365 -sha256 -extfile server.conf -extensions v3_req
    ``` 

## 理解ssl证书申请流程

## 客户端验证证书流程