# HTTPS证书

**生成根证书**

- 证书配置文件 ```conf
    [req]
    distinguished_name = req_distinguished_name
    prompt = no

    [req_distinguished_name]
    CN = github.com/penndev/wafcdn
    O = WAFCDN
    C = CN
    ```
- `openssl req x509 -nodes -days 3650 -newkey rsa:2048 -keyout private.key -out certificate.crt -config ssl.conf`


**签署某个域名**

```
# 创建服务端私钥
openssl genrsa -out example.com.key 2048

# 创建 CSR（填写域名信息）
openssl req -new -key example.com.key -out example.com.csr \
  -subj "/C=CN/ST=Test/L=Local/O=MyOrg/OU=Dev/CN=example.com"

根据csr来生成公钥
cert.conf 
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = example.com
DNS.2 = www.example.com


openssl x509 -req -in example.com.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial   -out example.com.crt -days 365 -sha256 -extfile cert.conf -extensions v3_req
```


