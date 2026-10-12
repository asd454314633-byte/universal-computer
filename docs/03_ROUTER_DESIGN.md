# 03_ROUTER_DESIGN.md — Capability Router

## 原则

先探测、后路由；每个任务只进入合理路径；禁止盲目轮询所有 Provider。

## 阶梯

```
browser: (webmcp[仅 opt-in 开启且站点暴露]) → playwright → visual[仅显式开启]
windows: com[仅任务声明 use_com] → uia → win32 → visual[仅显式开启]
```

## RouteDecision

```json
{"domain": "browser", "provider": "playwright",
 "reason": "structural DOM automation available (primary path)",
 "ladder": ["playwright", "visual"]}
```

## 行为细则

- `detect_all(force)`：逐 Provider 探测并缓存；detect 必须便宜、无副作用
  （不启动浏览器、不抢焦点、不弹窗）。
- 结构化 Provider 不可用时才顺阶梯下移；visual 默认 `visual_enabled=False`，
  显式开启后才可能被选为兜底（R3 验证了三段式：uia 禁→win32；uia+win32 禁+visual 关→none；
  visual 开→visual）。
- WebMCP 为实验性 opt-in：`--webmcp` 开启后仍需站点真实暴露才可用；
  不可用绝不导致任务失败（自动落到 Playwright）。
- UFO² 与 Stagehand 均未作为依赖引入；未来作为可选 Provider 接入时，
  必须实现本契约并注册进 factory，Core 不反向依赖它们。
