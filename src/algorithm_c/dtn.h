/*
 * dtn.h：資料結構與函式宣告。
 *
 * 對應 Python 版（src/algorithm/）：
 *   model.py    → curve.c（Curve、ramp、lag）
 *   validate.py → rules.c（stay_ok、三種節點規則、hop_ok、validate、commit）
 *   ours.py     → search.c（區間運算、candidate_range、solve_region、三個 filter、search、backtrack、plan）
 *
 * 和 Python 版唯一的行為差異：commit 直接修改 Problem（C 的習慣），
 * Python 版是回傳一個新的 Problem。
 */
#ifndef DTN_H
#define DTN_H

#include "rat.h"

/* ------------------------------------------------------------------ */
/* 區間清單：[(a0, b0), (a1, b1), ...]，每段都是閉區間                    */
/* ------------------------------------------------------------------ */
typedef struct {
    int n, cap;
    Rat *a, *b;
} IvList;

void iv_init(IvList *v);
void iv_free(IvList *v);
void iv_clear(IvList *v);
void iv_push(IvList *v, Rat a, Rat b);
void iv_copy(IvList *dst, const IvList *src);

/* ------------------------------------------------------------------ */
/* Curve：節點的 Buffer 占用曲線 O_n                                     */
/*   ts 變化點時刻（由小到大）、ls 左極限、rs 右極限                       */
/* ------------------------------------------------------------------ */
typedef struct {
    int n, cap;
    Rat *ts, *ls, *rs;
} Curve;

void curve_init(Curve *c);
void curve_free(Curve *c);
void curve_push(Curve *c, Rat t, Rat l, Rat r);
Rat  curve_left(const Curve *c, Rat t);
Rat  curve_right(const Curve *c, Rat t);
Rat  curve_top(const Curve *c, Rat t);
/* 嚴格落在 (a, b) 內的變化點：回傳個數，*first 設為第一個的位置（是連續的一段） */
int  curve_between(const Curve *c, Rat a, Rat b, int *first);
Rat  curve_peak(const Curve *c, Rat a, Rat b);
/* dst = dst + o（會刪掉共線的多餘點） */
void curve_add(Curve *dst, const Curve *o);

Rat ramp(Rat t, Rat a, Rat b, Rat S);

/* ------------------------------------------------------------------ */
/* 連線與問題                                                           */
/* ------------------------------------------------------------------ */
typedef struct {
    char id[24];
    int u, v;          /* 從 u 傳到 v */
    Rat a, b;          /* 開放時間 */
    Rat r;             /* 速率 MB/s */
    Rat d;             /* 傳播延遲 */
    IvList F;          /* 已預約的傳輸時段 */
} Contact;

typedef struct {
    int nc;            /* 連線數 */
    Contact *cs;
    int nn;            /* 節點數（節點編號 0 .. nn-1） */
    Curve *O;          /* O[n]：節點 n 的占用曲線 */
    int src, dst;      /* 目前這一包的來源、目的地 */
    Rat g, S, M, T;    /* 產生時間、大小、Buffer 上限、期限 */
    int ct;            /* 1 = 邊收邊轉，0 = 收完才轉 */
} Problem;

/* 排程：第 i 跳走連線 c[i]，在 s[i] 出發 */
typedef struct {
    int n;
    int *c;
    Rat *s;
} Schedule;

void sched_free(Schedule *s);

Rat lag(const Problem *P, const Contact *c1, const Contact *c2);
Rat arrival(const Problem *P, const Schedule *sch);

/* ------------------------------------------------------------------ */
/* rules.c                                                             */
/* ------------------------------------------------------------------ */
int  source_ok(const Problem *P, const Contact *c, Rat s);
int  relay_ok(const Problem *P, const Contact *c1, Rat s1, const Contact *c2, Rat s2);
int  destination_ok(const Problem *P, const Contact *c, Rat s);
int  hop_ok(const Problem *P, const Contact *c, Rat s);
int  validate(const Problem *P, const Schedule *sch);
void commit(Problem *P, const Schedule *sch);

/* ------------------------------------------------------------------ */
/* search.c                                                            */
/* ------------------------------------------------------------------ */
void subtract_open(const IvList *in, Rat x, Rat y, IvList *out);
void minus(const IvList *parts, const IvList *done, IvList *out);
void merge(IvList *v);
void candidate_range(const Problem *P, const Contact *c, Rat head, IvList *out);
/* 回傳 1 表示找到；找不到回傳 0 */
int  plan(const Problem *P, Schedule *out);

#endif
