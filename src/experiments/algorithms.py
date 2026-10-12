# 演算法入口：以名稱取得單包搜尋函式；預約與結果驗證仍由 runner 統一負責。
"""Routing plug-ins. Each call searches one bundle without reserving resources."""
from dataclasses import dataclass
from importlib import import_module
from typing import Callable


# 儲存演算法名稱、搜尋函式與剪枝設定；不包含任何網路資源狀態。
@dataclass(frozen=True)
class Algorithm:
    # name 是輸出識別，search 符合單包介面；disable_dominance 只供診斷用。
    name: str
    search: Callable
    disable_dominance: bool = False


# 解析內建名稱或受信任的本機 module:function；只回傳函式，不在此預約資源。
def resolve_algorithm(name):
    """Built-ins or a trusted local Python entry point, module:function."""
    from src.validation.proposed_v04 import search
    builtins = {
        'label_setting_v04': Algorithm('label_setting_v04', search),
        'label_setting_no_dominance': Algorithm(
            'label_setting_no_dominance', search, disable_dominance=True),
    }
    if name in builtins:
        return builtins[name]
    if ':' not in name:
        raise ValueError(f'Unknown algorithm: {name}; use a built-in or module:function')
    module, function = name.split(':', 1)
    try:
        # 這裡會執行匯入的本機 Python，不是解析純資料；僅用受信任的方法模組。
        implementation = getattr(import_module(module), function)
    except (ImportError, AttributeError, ValueError) as error:
        raise ValueError(f'Cannot load algorithm {name}: {error}') from error
    if not callable(implementation):
        raise ValueError(f'Algorithm entry point is not callable: {name}')
    return Algorithm(name, implementation)
