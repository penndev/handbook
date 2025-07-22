# HTTPS证书

**生成根证书**

- 生成证书配置文件 `ssl.conf`
    ```bash
    [req]
    distinguished_name = req_distinguished_name
    prompt = no

    [req_distinguished_name]
    CN = github.com/penndev/wafcdn
    O = WAFCDN
    C = CN
    ```
- 生成公私钥
  `openssl req x509 -nodes -days 3650 -newkey rsa:2048 -keyout private.key -out certificate.crt -config ssl.conf`


**签署某个域名**

1. 创建服务端私钥 
  `openssl genrsa -out example.com.key 2048` 
2. 创建CSR(域名信息)
    ```bash
    openssl req -new -key example.com.key -out example.com.csr -subj "/C=CN/O=ZuZhi/OU=DanWei/CN=example.com" -config ssl.conf
    ```
3. 证书配置文件 `cert.conf` 
    ```bash
    [ v3_req ]
    basicConstraints = CA:FALSE
    keyUsage = digitalSignature, keyEncipherment
    extendedKeyUsage = serverAuth
    subjectAltName = @alt_names

    [ alt_names ]
    DNS.1 = example.com
    DNS.2 = *.example.com
    ``` 
4. 根据私钥，中间证书文件，证书配置文件来生成公钥 
    ```sh
    openssl x509 -req -in example.com.csr -CA certificate.crt -CAkey private.key -CAcreateserial -out example.com.crt -days 365 -sha256 -extfile cert.conf -extensions v3_req
    ``` 
