# tenhou-convert — 天凤牌谱直转工具

将天凤牌谱从 [天凤](https://tenhou.net) 的原始 XML 格式直接转换为天凤观战 JSON 格式，一条命令搞定。

内部集成了 [@kobalab/tenhou-log](https://github.com/kobalab/tenhou-log)（XML → 电脑麻雀）和 [@kobalab/tenhou-url-log](https://github.com/kobalab/tenhou-url-log)（电脑麻雀 → 观战JSON），提供一个统一的接口。

## 安装

```sh
npm i -g @kobalab/tenhou-convert
```

或作为库使用：

```sh
npm i @kobalab/tenhou-convert
```

## 使用方式

### CLI

```sh
# 单牌谱转换
tenhou-convert 2016031822gm-0009-10011-896da481

# 从完整URL转换
tenhou-convert http://tenhou.net/0/log/?2016031822gm-0009-10011-896da481

# 指定某一局（0-based）
tenhou-convert --idx 0 http://tenhou.net/0/log/?2016031822gm-0009-10011-896da481

# 批量转换（输出JSON数组）
tenhou-convert <id1> <id2> <id3>
```

### Server

```sh
# 启动转换服务
tenhou-convert-server --port 8002 --baseurl /convert/

# 请求
curl http://127.0.0.1:8002/convert/2016031822gm-0009-10011-896da481
curl http://127.0.0.1:8002/convert/2016031822gm-0009-10011-896da481?idx=0
```

### 库函数

```javascript
const convert = require("@kobalab/tenhou-convert");

// 转换完整牌谱
convert("2016031822gm-0009-10011-896da481").then(json => {
    console.log(JSON.stringify(json));
});

// 只转换第0局
convert("http://tenhou.net/0/log/?2016031822gm-0009-10011-896da481", {
    idx: 0
}).then(json => {
    console.log(JSON.stringify(json));
});
```

## API

### convert(input, options)

- **input** `string` — 天凤牌谱ID 或完整URL
- **options** `object`
  - **idx** `number` — 指定局索引（0-based），省略则转换全部
  - **rule** `object` — 规则描述（默认 `{disp:"电脳麻雀",aka:1}`）
  - **title** `string` — 自定义标题（默认使用牌谱ID）
- 返回值 `Promise<object>` — 天凤观战JSON格式

## 许可证

[MIT](https://github.com/kobalab/tenhou-convert/blob/master/LICENSE)

## 作者

[Satoshi Kobayashi](https://github.com/kobalab)
