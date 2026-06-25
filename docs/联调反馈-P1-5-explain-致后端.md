# 联调反馈 · P1-5 AI 方案解释（致后端）

| 字段 | 值 |
| --- | --- |
| **阶段** | P1-5 / F015 |
| **前端分支** | `frontend/p1-5-p1-01` @ `fbcb78c` |
| **后端分支** | `origin/backend/phase-p1-5` @ `08b5d47` |
| **集成分支** | `integration/p1-5-explain` @ `84123bb` |
| **文档日期** | 2026-06-09 |
| **联调状态** | API 冒烟通过 + 前端 build 通过 |

---

## 1. 前端 API 适配（integration/p1-5-explain）

| 项 | 前端原契约 / Mock | 真实 API 适配 |
| --- | --- | --- |
| 请求 | `{ schedule_code, detail_level? }` | 仅传 `{ schedule_code }` |
| 响应 `key_decisions` | 无（Mock 用 `sections.reasoning` 字符串） | → `sections.key_decisions[]` |
| 响应 `potential_risks` | `sections.risks` | 直映射 |
| 响应 `suggestions` | `sections.suggestions` | 直映射 |
| `schedule_code` 回显 | 响应体内 | 由请求参数回填（后端 data 不含） |
| 超时 | 60s | 70s（对齐 DeepSeek 上限） |

改动文件：[`ai.ts`](src/frontend/src/api/ai.ts)、[`types/ai.ts`](src/frontend/src/types/ai.ts)、[`ExplainResultBody.vue`](src/frontend/src/components/ai/ExplainResultBody.vue)

---

## 2. 联调环境

- `.env.local`：8 项 Mock 全 `false`
- DB：`python -m scripts.init_demo_data`（**不预置 GlobalSchedule**，需先造方案）
- 登录：`dispatcher` / `123456`
- 后端：`uvicorn main:app --port 8000`
- 前端：`npm run dev`

**造数前置**：Dashboard 方案下拉为空时，先 `POST /schedule/global` preview+confirm，或通过 AI 助手生成 draft 并确认采用。

---

## 3. API 冒烟结果（`scripts/test_p1_5_explain_integration.py`）

```
health ok
login ok
schedule created GS20260625001
explain ok degraded= False explanation_len= 311
missing params ok 40001
not found ok 40401
ALL_P1_5_EXPLAIN_API_CHECKS_PASS
```

| 场景 | 步骤 | 结果 |
| --- | --- | --- |
| 健康检查 | `GET /api/health` | 通过 |
| 登录 | `POST /api/auth/login` | 通过 |
| 造数 | preview+confirm 2 个 pending 订单 | `GS20260625001` |
| 正常 explain | `POST /api/ai/explain` | `code=0`；四字段齐全；`degraded=false` |
| 参数缺失 | `{}` | `40001` |
| 方案不存在 | `GS_NONEXISTENT` | `40401` |

---

## 4. 手测清单（UI）

| 项 | 状态 | 说明 |
| --- | --- | --- |
| 未选方案点「方案解释」 | 待手测 | 预期 warning「请先在上方选择要解释的方案」 |
| 选中方案 → 方案解释 | 待手测 | 预期抽屉展示摘要 + 关键决策 + 风险 + 建议 |
| DeepSeek 降级 | API 已覆盖 | 后端 exception 路径返回 `meta.degraded=true` |
| loading / 超时 | 待手测 | axios timeout 70s |
| `npm run build` | **通过** | vue-tsc + vite build 无错误 |

> API 层与 adapter 已验证；UI 手测需在浏览器登录 Dashboard 后确认抽屉渲染（结构与 Mock 一致，数据源改为真实 API）。

---

## 5. 非阻塞建议（致后端）

1. 响应 `data` 中回传 `schedule_code`，减少前端回填
2. 将 [`api-contract-p1-5.md`](docs/api-contract/api-contract-p1-5.md) 合入 main，与实现对齐
3. F016/F017 后端已实现，前端仍为占位按钮；后续 P1 迭代可单独联调

---

## 6. 结论

- **API 层**：F015 explain 正常流 + 参数校验 + 404 冒烟通过
- **前端层**：adapter + build 通过；UI 抽屉手测待浏览器确认
- **建议**：adapter 提交可 cherry-pick 至 PR #36 后合并 main
