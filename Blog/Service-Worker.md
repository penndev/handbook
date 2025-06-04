## Worker

> Worker适合用来运行cpu密集型任务 它的代码运行在后台线程，通过回调方式与DOM交互。
通过`if (window.Worker)`验证是否支持Worker。Worker进程随着网页的关闭而关闭。



**`const w = new Worker(aURL, options);`**

- `aURL`: 是一个 DOMString 表示 worker 将执行的脚本的 URL。它必须遵守同源策略
- `w.postMessage()` 发送数据到`worker`的`onmessage`
- `w.onmessage` 从`worker`的`postMessage`接收数据

- `importScripts` 子 worker

```js
const workerCode = `
  self.onmessage = function(e) {
    const result = e.data * 2;
    self.postMessage(result);
  };
`;

const worker = new Worker(
  URL.createObjectURL(
    new Blob([workerCode], { type: "application/javascript" })
  )
);
// 发送给workerCode onmessage
worker.postMessage(1);
// 获取回调结果
worker.onmessage = function (e) {
  console.log("结果是:", e.data); // 输出 结果是: 10
};
// 结束后台worker
worker.terminate();
```

## Service Worker

> Service Worker不仅有Worker的特性，而且启动后可以不依赖页面继续运行，同时可以多个页面可共享一个 Service Worker
适用于离线支持、PWA、缓存优化、后台推送等。	


| 特性             | Service Worker                          | Web Worker                            |
|------------------|------------------------------------------|----------------------------------------|
| 用途             | 拦截网络请求、离线缓存、推送通知等      | 执行耗时 JavaScript 运算               |
| 生命周期         | 独立于页面，后台运行                     | 随页面生命周期结束                     |
| 启动方式         | 浏览器注册并按需启动                     | 页面中通过 `new Worker()` 启动         |
| 网络拦截         | ✅ 支持，可拦截 `fetch` 请求              | ❌ 不支持                               |
| 缓存管理         | ✅ 使用 Cache API                        | ❌ 不支持                               |
| 推送通知         | ✅ 支持（结合 Push API）                 | ❌ 不支持                               |
| 跨页面共享       | ✅ 多个页面可共享一个 Service Worker     | ❌ 每个页面实例独立                    |
| 访问 DOM         | ❌ 不可直接访问 DOM                      | ❌ 同样不可访问 DOM                    |
| 通信方式         | `postMessage` 与页面通信                 | `postMessage` 与主线程通信             |
| 适用场景         | 离线支持、PWA、缓存优化、后台推送       | 计算密集型任务，避免主线程阻塞         |


