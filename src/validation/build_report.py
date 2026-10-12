# 由已保存的驗證資料產生歷史報告，不手填抵達時間或通過數量。
"""Render verified values from raw JSON/CSV; never type in result numbers."""
from pathlib import Path
from hashlib import sha256
import json
import csv
from .build_walkthrough import table

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output'/'validation'
DOC=ROOT/'docs'


# 核對凍結文件雜湊與已保存答案，再由資料生成驗證報告。
def run():
    results=json.loads((OUT/'oracle_results.json').read_text(encoding='utf-8'))
    dom=json.loads((OUT/'dominance_results.json').read_text(encoding='utf-8'))
    gate=json.loads((OUT/'comparison_gate.json').read_text(encoding='utf-8'))
    originals=json.loads((OUT/'frozen_document_hashes.json').read_text(encoding='utf-8'))
    changed=[name for name,old in originals.items() if sha256((DOC/name).read_bytes()).hexdigest()!=old]
    if changed:raise AssertionError('Frozen source files changed: '+repr(changed))
    rows=[]
    for r in results:
        p,o=r['proposed'],r['oracle']
        rows.append([r['case']+'/'+r['bundle'],p['arrival'] is not None,o['arrival'] is not None,
                     p['arrival'] or '—',o['arrival'] or '—',r['match']])
    # Zero arrival is a real answer, never render it as missing.
    for row,r in zip(rows,results):
        row[3]='—' if r['proposed']['arrival'] is None else r['proposed']['arrival']
        row[4]='—' if r['oracle']['arrival'] is None else r['oracle']['arrival']
    sections=['# Independent oracle validation v01',
              '## Oracle independence',
              '`exhaustive_oracle.py` 僅 import fractions、itertools、collections、copy。AST 測試確認沒有 import proposed search / extension / dominance / occupancy / commit。共用輸入資料格式，但不共用可行性 helper。',
              'Oracle 先列出所有拓樸 walks（允許重訪）至可證明的正時間 hop bound；再對每條 route 列舉各 contact start slots 的 Cartesian product。每個完整 schedule 才重算 timing、per-contact 用量及全路徑 inventory，沒有 dominance、prefix buffer pruning 或 incumbent branch-and-bound。',
              'Proposed 使用局部收發曲線；oracle 使用完整 schedule 的 per-visit inventory 公式，然後在全部事件端點求總占用。兩者都使用 Fraction 與相同事件峰值模型，以免把語意不同混成演算法差異。',
              '## 同模型正確性比較',table(['Case','Proposed Feasible?','Oracle Feasible?','Proposed Arrival','Oracle Arrival','Match'],rows),
              '案例 01–06 對應使用者要求的六類；07–14 增加 boundary、δ、接收／發送超量、source=destination、source滿、必要循環、重複 quota、交付瞬間峰值。',
              '## 每個案例的完整輸入與證據',
              '人工重算用的逐案例 contact / bundle / buffer 表，見 [validation_case_catalog_v01.md](validation_case_catalog_v01.md)。',
              '所有 contacts、bundles、buffers、O 曲線、每次 snapshot、proposed trace、oracle feasible schedules、拒絕原因及 witness，均保存在 `output/validation/oracle_results.json`。手工定義來源是 `validation_cases.py`。',
              table(['Case / bundle','Topological walks','Complete schedules','Feasible schedules','Expected arrival'],
                    [[r['case']+'/'+r['bundle'],r['oracle']['paths_considered'],r['oracle']['schedules_considered'],len(r['oracle']['feasible_schedules']),r['expected']] for r in results]),
              '## Dominance OFF / ON（相同 query snapshot）',
              'Labels 欄位定義為 enqueued（含來源）；另列 created（包含立即被 pruning 的候選）、expanded，避免只選有利數字。比較最優值，不強制最優路徑唯一；是否同一路徑另外記錄。',
              table(['Case','Arrival OFF','Arrival ON','Labels OFF','Labels ON','Created OFF/ON','Expanded OFF/ON','Same optimal value?','Same route?'],
                    [[r['case']+'/'+r['bundle'],r['off']['arrival'],r['on']['arrival'],r['off']['stats']['enqueued'],r['on']['stats']['enqueued'],
                      str(r['off']['stats']['created'])+'/'+str(r['on']['stats']['created']),str(r['off']['stats']['expanded'])+'/'+str(r['on']['stats']['expanded']),r['same_optimal_value'],r['same_route']] for r in dom]),
              '這是 correctness/pruning 觀察，不是 runtime、memory 或大規模 performance benchmark。Sequential queries 使用同一已接受 canonical schedule 建構下一快照，oracle 以獨立 commit 重建並核對；不讓 tie 選不同路徑造成第二包輸入不同。',
              '## Sequential reservation 的因果對照',
              '相同第二包與 contact plan，未提交第一包時選 c3→c2、arrival=8；提交後選 c4→c5、arrival=12。測試亦核對 B@2.5 的占用=2、B@4=4、B@8=0，與未選 c5 在第一包後 quota 仍為 4。',
              '## 模型邊界 witness',
              '`counterexample_grid_continuous.json` 保存同一網路的 Δ=1 與 Δ=1/2 結果，分別 4、7/2。每種格點上 proposed=oracle；連續時間 witness 與最優下界推導見 search_completeness_review_v01.md。這不是將演算法改成 event-based。',
              '## 停止條件',
              f"目前 gate={gate['status']}；未發現同模型 oracle mismatch。程式若發現 mismatch 會保存 counterexample JSON、將 gate 設 STOP 並拒絕後續 dominance comparison；不會自動修演算法。",
              '## 限制',
              '14 個人工案例／15 次查詢與 18 項測試，不是任意規模或所有輸入的機械證明。輸入驗證也不是 production-grade；負 buffer、無效既有 O、radio/custody 的實務驗證尚不完整。',
              '## 重現指令',
              '於專案根目錄，以可用 Python 執行：',
              '```text\npython -m src.validation.compare_oracle\npython -m src.validation.compare_dominance\npython -m unittest discover -s tests -v\npython -m src.validation.build_report\npython -m src.validation.render_figures\n```',
              '首次產生 walkthrough 使用 `python -m src.validation.build_walkthrough`；重新執行時核對既有 freeze manifest，不覆寫凍結來源。Python 實際路徑與執行記錄見 output/validation/reproducibility.json。']
    (DOC/'oracle_validation_v01.md').write_text('\n\n'.join(sections),encoding='utf-8')
    catalog=['# Validation case catalog v01',
             '資料量 MB、時間秒、rate MB/s。所有案例 Δ=1；T 各表列出。背景曲線每列 (t0,t1,y0,y1) 表示一段線性占用；同一曲線的接點不重複計數。既有曲線是 query snapshot，未列曲線的 node 初始為 0。',
             'Oracle 沒有將這些背景曲線當成新的決策。walkthrough 第二包繼承第一包的完整預約，沒有 reset。完整數值由 oracle_results.json 自動抽取。']
    seen=set()
    for r in results:
        if r['case'] in seen:continue
        seen.add(r['case']);case=r['input']
        catalog += ['## '+r['case'],f"Δ={case['delta']}，T={case['horizon']}。",
                    table(['Contact','From','To','Start','End','Rate','Propagation','Quota'],
                          [[c[k] for k in ('id','u','v','start','end','rate','delay','quota')] for c in case['contacts']]),
                    table(['Bundle','Source','Destination','Generation','Size'],
                          [[b[k] for k in ('id','source','dest','g','size')] for b in case['bundles']]),
                    table(['Node','Buffer'],sorted(case['buffers'].items()))]
        bgrows=[[v,i,'; '.join(str(tuple(seg)) for seg in curve)]
                for v,curves in case['background'].items() for i,curve in enumerate(curves)]
        catalog.append(table(['Node','Curve ID','Segments (t0,t1,y0,y1)'],bgrows) if bgrows else '初始背景占用為 0。')
        for query in [item for item in results if item['case']==r['case']]:
            catalog += [f"### {query['bundle']} oracle 的所有可行格點排程",
                        table(['Contact/start sequence','Arrival'],[[str(s['hops']),s['arrival']] for s in query['oracle']['feasible_schedules']])
                        if query['oracle']['feasible_schedules'] else '沒有可行格點排程；拒絕 witness 見原始 JSON。']
    (DOC/'validation_case_catalog_v01.md').write_text('\n\n'.join(catalog),encoding='utf-8')
    summary='''# Algorithm validation summary v01

## 結果
已完成 frozen v04 correctness audit：兩包逐步 trace、兩類 dominance 例子、extension/dominance 論證、completeness 盤點、獨立 exhaustive oracle、ON/OFF 比較與 calendar gap。沒有修改原始 v04 或加入 event-based/calendar 搜尋。

## Confirmed Correct（在明列假設下的論證）
- Extension 的 sender/receiver 分段占用檢查可維持可行前綴 invariant。
- 同 node/query 的等待橋接與 U componentwise comparison，支持 continuation-preserving dominance。
- Source、destination、propagation、quota 累計與提交均在手算與測試中核對。
- 這些結論依賴固定預約、無 copies、無額外路徑歷史限制及 snapshot 所列事件約定。

## Verified Only Under Finite Grid Model
- 14 個案例、15 次查詢：proposed 與 independent oracle 的可行性／最優 arrival 一致。
- Dominance ON/OFF 全部維持最優值；Case 05 入列 labels 從 7 減至 3；walkthrough 第二包從 7 減至 5。
- 18 個 unittest tests 通過；原始 test_results.txt 可重現。有限測例不是一般性正確證明。

## Not Yet Proven
- Continuous-time successor enumeration 與全域 completeness。
- 有限事件表示能否完整且有效率地壓縮所有必要 labels。
- 記憶體、runtime 或大網路的效能優勢；本次沒有執行這些比較。
- 同時 generation/delivery 的硬體事件語意尚未唯一決定；目前採保守峰值約定。

## Known Counterexamples
| ID | 被推翻的主張 | Witness | 是否為 frozen v04 同模型錯誤 |
|---|---|---|---|
| CE-EARLY | 早到即可刪晚到 | B@2 無法跨越既有占用，B@8 可繼續 | 否，v04 已有等待條件 |
| CE-GRID-01 | 整數資料即代表整數格點等於連續最優 | Δ=1 arrival=4；continuous witness=7/2 | 否，v04 保證明限 grid |
| CE-CALENDAR-01 | Quota 足夠即可排入連續傳輸 | 3 MB 剩餘分成三個 1 秒空檔，2 MB 包無法連續傳 | 否，calendar 不在當前模型 |

未發現 frozen v04 在本次同模型比較中的反例，**不代表不存在尚未測到的反例**。以上 witness 保留，沒有為讓結果好看而變更演算法。

## Missing Components
- Continuous-time exact extension / search 定義與證明。
- Contact transmission calendar，以及共用 radio（若要納入）的資料与約束。
- Production input validation、custody/retransmission copy 模型（若要納入）。
- 更廣輸入的測試與效能比較；必須在模型及正確性問題先確立後進行。

## 候選修正方案（未採用，需使用者確認）
1. 保留 finite-grid problem 作正式第一階段問題，清楚限定保證。
2. 研究依 buffer 線性交點與可行 departure intervals 生成候選時間；不可只列原始事件點。
3. 增加 Ω_c 與連續 free-window 檢查，另建同模型 oracle，再與 2024 方法公平比較。

## Ready for Advisor Discussion
可以展示：固定問題定義、逐步 label trace、前包如何改變後包路徑、pruning 的可取代性證明、測試結果以及尚未解決的兩個模型邊界。
不能宣稱：已完成連續時間最優路由、已等價解決 2024 完整排程問題、首次提出 Label Setting、或比既有方法快。

## 文件與證據索引
- [Current snapshot](current_algorithm_snapshot_v01.md)
- [完整 walkthrough](algorithm_walkthrough_v01.md)
- [兩種 dominance 例子](dominance_examples_v01.md)
- [Extension review](extension_correctness_review_v01.md)
- [Dominance review](dominance_correctness_review_v01.md)
- [Search completeness](search_completeness_review_v01.md)
- [Oracle 與 ON/OFF 表格](oracle_validation_v01.md)
- [全部測例輸入與可行排程](validation_case_catalog_v01.md)
- [Calendar gap](transmission_calendar_gap_v01.md)
- 原始數字／JSON／CSV：`output/validation/`
- 程式：`src/validation/`；測試：`tests/`
- 九張同拓樸 PNG：`figures/algorithm_walkthrough/`

## 檔案保全
原始演算法與歷史研究文件未改；SHA-256 清單與核對結果在 output/validation。新增驗證實作忠實保留 v04 定義；開發時曾修正報告輸出根目錄的程式路徑錯誤，非演算法或判別式修改。
'''
    (DOC/'algorithm_validation_summary_v01.md').write_text(summary,encoding='utf-8')
    provenance=dict(python_executable=__import__('sys').executable,root=str(ROOT),
                    source_unchanged=not changed,frozen_files_checked=len(originals),
                    arithmetic='fractions.Fraction',tests=18,queries=len(results),
                    performance_benchmarks=False,algorithm_changes=False,
                    code_files={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src'/'validation').glob('*.py')})
    (OUT/'reproducibility.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    witnesses=[dict(id='CE-EARLY',scope='invalid simplification, not frozen v04',
                    definition='delete later label solely because arrival is later',
                    evidence='oracle_results.json / 04_late_label',candidate_fix='retain frozen waiting feasibility test'),
               dict(id='CE-GRID-01',scope='continuous-time completeness outside grid guarantee',
                    definition='enumerate s only in delta*Z',evidence='counterexample_grid_continuous.json',
                    grid_arrival='4',continuous_optimum='7/2',candidate_fix='derive exact feasible departure regions; not implemented'),
               dict(id='CE-CALENDAR-01',scope='calendar scheduling outside aggregate model',
                    window=[0,6],rate=1,residual_quota=3,size=2,
                    busy=[[1,2],[3,4],[5,6]],maximum_free_duration=1,
                    definition='quota/window do not check busy intervals',
                    candidate_fix='add fixed busy calendar and continuous-free-interval test; not implemented')]
    (OUT/'counterexamples_index.json').write_text(json.dumps(witnesses,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Reports generated; frozen source files unchanged:',len(originals))

if __name__=='__main__':run()
