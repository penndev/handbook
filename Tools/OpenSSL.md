

## 加解密

```bash
openssl aes-128-cbc -e -in <Decrypt.txt> -out <Encrypt.txt> -K <HEX([16]byte)> -iv <HEX([16]byte)>
openssl aes-128-cbc -d -in <Encrypt.txt> -out <Decrypt.txt> -K <HEX([16]byte)> -iv <HEX([16]byte)>
```

 ## 生成证书

 ## 分析证书