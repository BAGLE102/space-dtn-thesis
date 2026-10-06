# Walkthrough figures

九張 PNG 為 2560×1440（16:9），使用固定拓樸與固定 contact 位置。文字使用標楷體（DFKai-SB / kaiu.ttf），缺少的特殊符號以 DejaVu Sans 補足。

- step_00_topology.png
- step_01_source_label.png
- step_02_first_extension.png
- step_03_feasibility_check.png
- step_04_dominance.png
- step_05_bundle1_route.png
- step_06_resource_update.png
- step_07_bundle2_search.png
- step_08_final_state.png

step_04 的 Bundle 1 不觸發 pruning；step_07 才顯示 Bundle 2 的實際 pruning。紅色 c5 等待失敗屬 B@2 label 的延伸，不代表整個 c5 不可用。

使用 `python -m src.validation.render_figures` 重建。matplotlib 安裝於專案 tmp/validation_plot_dependencies，未更改系統 Python。