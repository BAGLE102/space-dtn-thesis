"""結果檔續跑與失敗即停的共用工具（不影響演算法）。"""
import json
import os
import sys


def load_done(path, key):
    """讀已完成的結果，回傳 key(r) 的集合。

    最後一行若被中斷而不完整，會把那一行連同同一組（同一個 key）已寫入的行一起截掉，
    讓續跑時整組重跑；一組多行（例如一個案例多包）時也不會只留一部分。
    中間若有壞行，直接停止，請人工檢查。
    """
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, "rb") as fh:
        data = fh.read()
    good_end = 0
    ends = []  # (key, 該行結束位置)
    lines = data.split(b"\n")
    for n, line in enumerate(lines):
        if not line.strip():
            good_end += len(line) + 1
            continue
        try:
            r = json.loads(line.decode("utf-8"))
        except ValueError:
            if n == len(lines) - 1 or all(not x.strip() for x in lines[n + 1:]):
                if ends:
                    last = ends[-1][0]
                    while ends and ends[-1][0] == last:
                        ends.pop()
                    done.discard(last)
                    good_end = ends[-1][1] if ends else 0
                print("結果檔最後一行不完整，已截掉並重跑該組：%s" % path, flush=True)
                with open(path, "r+b") as fh:
                    fh.truncate(good_end)
                break
            sys.exit("結果檔中間有壞行（第 %d 行），請人工檢查：%s" % (n + 1, path))
        done.add(key(r))
        good_end += len(line) + 1
        ends.append((key(r), good_end))
    return done


def stop_if_validation_failed(rows, label):
    """本方法產生的排程若未通過獨立回放驗證，立刻停止整個流程。"""
    bad = [x for x in rows if x.get("why") == "VALIDATION_FAILED"]
    if bad:
        sys.exit("驗證失敗，停止：%s，第 %s 包" % (label, ",".join(str(x["i"]) for x in bad)))
