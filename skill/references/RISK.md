# RISK.md — 风险分级与用户权限原则

## 继承的用户全局原则（宿主必须遵守）

**普通、可恢复操作 → 默认执行；高风险不可逆操作 → 最终动作前确认。**

不要每一步都确认。以下动作**不因需要确认而停下**：
点击、输入、打开网页、打开软件、运行普通命令、创建文件、修改项目文件。

以下 8 类属于 DESTRUCTIVE，**最终不可逆一步之前**必须向用户确认：
1. 永久删除重要数据 / 不可恢复资产
2. 覆盖唯一原件且无备份
3. 支付 / 转账 / 购买等真实资金
4. 对外发布 / 群发 / 重要不可撤回信息
5. 修改 Windows / 网络 / 安全策略等系统级关键配置
6. 安装显著改变系统环境的大型高危依赖
7. 账户安全 / 凭据 / 提权
8. 其他明显不可逆操作

## Core 的风险声明模型

Core 只**声明**每个动作的风险等级；是否/如何确认由调用宿主决定
（Core 内部禁止宿主专属确认 UI）。

```
READ        浏览、读文本、截图、快照、列窗口、读树、聚焦
WRITE       fill、click、set_text、invoke、type_text、upload、download
DESTRUCTIVE delete、overwrite、pay、submit_irreversible、
            send_external、kill_process
```

- 未知动作默认按 WRITE 声明。
- task step 的 `risk` 字段只能**升级**不能降级（如点击"提交订单"按钮
  应声明为 DESTRUCTIVE）。
- WRITE / DESTRUCTIVE 默认 `requires_confirmation=true`，但按上述用户
  原则，宿主对 WRITE 直接放行；仅 DESTRUCTIVE 走确认。
- DESTRUCTIVE 未确认时 Core 返回 `PERMISSION_DENIED`；宿主确认后带
  `risk` 覆盖重发即可执行。

## 审计

所有动作（无论风险等级）逐条写入 JSONL 审计日志，字段含
`task_id/provider/action/target/result/duration/recovered/error`。
确认类动作额外记录确认来源（用户批准 / 规则放行）。
