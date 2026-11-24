"""結果檔續跑與失敗即停的共用工具（不影響演算法）。

規則：
- 主結果檔只放「完整且通過驗證」的組。驗證失敗的紀錄寫到 <out>.failed.jsonl，不算完成。
- 啟動時重新整理主結果檔：只保留完整的組；不完整的組（例如一個案例只寫了一部分包）、
  被中斷的最後一行、帶驗證失敗的組，都從主檔移除，續跑時整組重跑。
- 檔案中間若有無法解析的行，直接停止，請人工檢查。
"""
import json
import os
import sys


def failed_path(out):
    return out + ".failed.jsonl"


def load_done(path, key, complete=lambda rows: True):
    """回傳已完成的 key 集合，並把主結果檔整理成只含完整的組。

    complete(rows)：同一個 key 的所有行是否構成完整且合格的一組。
    """
    if not os.path.exists(path):
        return set()
    with open(path, "rb") as fh:
        raw = fh.read().split(b"\n")
    groups, order = {}, []
    for n, line in enumerate(raw):
        if not line.strip():
            continue
        try:
            r = json.loads(line.decode("utf-8"))
        except ValueError:
            if all(not x.strip() for x in raw[n + 1:]):
                print("結果檔最後一行不完整，該組將重跑：%s" % path, flush=True)
                break
            sys.exit("結果檔中間有壞行（第 %d 行），請人工檢查：%s" % (n + 1, path))
        k = key(r)
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(r)
    # 被截斷那一行所屬的組無法得知，所以最後一組一律要通過 complete 才保留
    keep = [k for k in order if complete(groups[k])]
    dropped = len(order) - len(keep)
    if dropped:
        print("移除 %d 組不完整或不合格的紀錄，將重跑：%s" % (dropped, path), flush=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for k in keep:
            for r in groups[k]:
                fh.write(json.dumps(r) + "\n")
    os.replace(tmp, path)
    return set(keep)


def no_validation_failure(rows):
    return all(x.get("why") != "VALIDATION_FAILED" for r in rows for x in r.get("rows", []))


def record_failure_and_stop(out, record, msg):
    """把失敗的那一組寫到 <out>.failed.jsonl（主檔不寫），然後停止。"""
    with open(failed_path(out), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    sys.exit("驗證失敗，停止：%s（紀錄在 %s）" % (msg, failed_path(out)))
