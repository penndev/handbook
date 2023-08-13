
# GIT使用技巧

## 密码存储方式

账号密码存储
```
git config --local credential.helper store
git config --global credential.helper store
```

## 墙内配置host加速

国内服务器加速
```
/etc/hosts
140.82.112.3 github.com
185.199.108.153 assets-cdn.github.com
199.232.69.194 github.global.ssl.fastly.net
```

## Git子树提交到github gh-pages

```bash
git push origin --delete gh-pages
git subtree push --prefix dist origin gh-pages
```