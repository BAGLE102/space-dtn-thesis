# Codex效率與上下文用量設定

2026-10-20。已查官方文件、第三方原始專案與本機設定，並完成可回復的調整。未更改模型、reasoning effort、研究演算法或既有插件啟用狀態。

## 工具選擇

| 工具 | 作用與代價 | 本次處理 |
| --- | --- | --- |
| [RTK](https://github.com/rtk-ai/rtk) | 壓縮常見CLI輸出，減少進入上下文的重複文字；摘要可能省略細節 | 安裝OSS 1.0.1，僅用於一般狀態查詢 |
| [Serena](https://github.com/oraios/serena) | 按程式符號檢索及編輯，適合較大程式庫；有語言伺服器與MCP的設定／工具開銷 | 本次不安裝；目前先用已具備的rg與局部讀檔 |
| [Context7](https://github.com/upstash/context7/blob/master/docs/clients/codex.mdx) | 查詢最新函式庫文件，能減少猜API與反覆查詢；不是通用token壓縮器 | 插件目錄查到可用但未安裝；需要套件文件時再啟用 |
| [Codex Skills](https://learn.chatgpt.com/docs/build-skills) | 官方採按需載入完整指引；技能數量本身不等於節省 | 不批次加裝技能包；只讀符合任務的skill |

第三方工具的效能描述是作者主張，未推定在本專案必然節省相同比例。沒有設置API代理，也沒有修改登入方式或憑證。

## 已完成設定

1. 安裝作者GitHub Release的Windows x86_64 **RTK OSS v1.0.1**，位於 `%USERPROFILE%/.codex/tools/rtk/rtk.exe`，`--version`與唯讀Git命令均成功。
2. 下載檔SHA-256與GitHub資產digest一致：`0e53e2eca471e15fbd3636e64e6bc0b182cbc278ed0339c80450a2dd03f4cd6b`。這確認下載完整性，不代表完整程式安全審計。
3. 在使用者 `%USERPROFILE%/.codex/config.toml` 設 `tool_output_token_limit = 4000`。原檔備份於 `%USERPROFILE%/.codex/backups/codex-efficiency-20261020/`；備份不提交Git。
4. 專案AGENTS加入局部搜尋、按需讀檔、摘要查詢、保留錯誤證據與避免重複測試的規則。

依[官方設定說明](https://learn.chatgpt.com/docs/config-file/config-reference)，`tool_output_token_limit`限制個別工具／函式回傳存入歷史的token預算。這不是整段對話或帳戶消費上限，也不保證所有工具介面會用相同方式套用。新設定須以重新開啟Codex／新工作階段的生效情況為準；已存在的長對話不會被追溯縮短。

沒有執行 `rtk init`，因此未安裝全域自動命令重寫hook。Codex須依AGENTS顯式使用RTK；其他終端命令不會全部自動被壓縮。避免以自動過濾結果取代研究正確性核對。

## 本機小測試

| 同一組唯讀命令參數 | 原始stdout | RTK stdout | 輸出位元組減少 |
| --- | ---: | ---: | ---: |
| git status | 275 bytes | 76 bytes | 72.4% |
| git log -8 | 1,781 bytes | 790 bytes | 55.6% |

兩組原始與RTK命令退出碼均為0。量測在本次專案文件修改前執行；輸出長度會隨Git狀態改變。這不是具代表性的工作負載測試，也未證明摘要與原文在所有語義上等價。

**以上僅是stdout位元組數，不是實際tokenizer計數、總帳單或帳戶額度節省。** RTK原始README也說明其token數是近似估算，終端輸出僅占整體上下文的一部分。實際長期節省尚未量測。

## 使用與回復

```powershell
& "$env:USERPROFILE/.codex/tools/rtk/rtk.exe" git status
& "$env:USERPROFILE/.codex/tools/rtk/rtk.exe" git log -8
```

數學定義、測試失敗、完整diff與反例判讀使用原始內容；長log存檔後按錯誤位置讀取。不要只因RTK摘要沒有顯示錯誤就判定驗證通過。

要停用：移除使用者config新增的 `tool_output_token_limit`，或在確認沒有較新的設定修改後選擇備份還原；移除AGENTS的RTK建議即可停止顯式使用。未改PATH、未註冊服務、未安裝自動重寫hook，不需改回系統shell。

本機安裝檢查資料在 `tmp/codex_efficiency_20261020/installation_check.json`（不提交）；重現本機測試需在原始與RTK命令各自以相同參數擷取stdout後計算bytes。
