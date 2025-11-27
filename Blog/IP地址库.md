# IP地址库GEOIP

## [纯真IP地址库](https://www.cz88.net/)


qqwry.dat ~~纯真IP库数据qqwry.dat数据（官方在 2024 年 10 月份已停止维护，官方已无发布dat格式文件。）~~

https://github.com/penndev/gopkg/tree/main/qqwry 这个库有对 qqwry.dat 数据格式的解析


参考程序库 

czdb 最新的纯真数据库文件，包含了IPv4和IPv6纯真的数据经过笔者对比，大陆的数据相对来说更新频率和全面会比其他的准确性，及时性强很多。

**授权**

社区版 https://www.cz88.net/geo-public 从这里只要推广纯真IP就可以获取免费授权，如果纯真IP为你带来了商业价值请购买商业版进行补票（XD）。



**数据包拆解**

czdb用B-tree索引，但是中间还有加密部分。

需要进行拆包


https://github.com/penndev/gopkg/tree/main/test/czdb 对czdb的数据进行拆分为geoip列表的txt文件，然后用 https://github.com/lionsoul2014/ip2region/tree/master/maker 工具进行xdb的数据库文件封装

- xdb授权 Apache-2.0 license 
- 纯真IP授权规定。 请用户自己重新生成自己的czdb与xdb文件，避免授权纠纷
```
1.纯真社区版IP库离线版免费提供，并非商业数据库。我们不对该数据库承担任何除服务可用性外的责任。因该IP库的数据准确性等所造成问题，我们不承担任何责任。请您谨慎选择使用。

2.纯真将定期查询您提交的展示纯真信息的网页或者APP页面。若发现相关页面已经失效或者修改为无关信息，我们有权停止您使用纯真社区版IP库更新服务。

3.纯真社区版IP库仅授权给您使用，每个授权用户均有自己独特的下载链接，若发现您擅自公开、转让该链接给其他方使用，我们有权停止您使用纯真社区版IP库更新服务，并追究您的相关责任。
```

用法参考:

https://github.com/penndev/gopkg?tab=readme-ov-file#ip2region


## GEO-Lite