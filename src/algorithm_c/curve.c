/*
 * curve.c：區間清單、Curve（O_n）、ramp、lag。對應 Python 的 model.py。
 */
#include <string.h>
#include "dtn.h"

static void *xrealloc(void *p, size_t n) {
    void *q = realloc(p, n);
    if (!q && n) { fprintf(stderr, "記憶體不足\n"); exit(2); }
    return q;
}

/* ================================================================== */
/* 區間清單                                                            */
/* ================================================================== */

void iv_init(IvList *v) { v->n = v->cap = 0; v->a = v->b = NULL; }
void iv_free(IvList *v) { free(v->a); free(v->b); iv_init(v); }
void iv_clear(IvList *v) { v->n = 0; }

void iv_push(IvList *v, Rat a, Rat b) {
    if (v->n == v->cap) {
        v->cap = v->cap ? v->cap * 2 : 4;
        v->a = xrealloc(v->a, sizeof(Rat) * v->cap);
        v->b = xrealloc(v->b, sizeof(Rat) * v->cap);
    }
    v->a[v->n] = a;
    v->b[v->n] = b;
    v->n++;
}

void iv_copy(IvList *dst, const IvList *src) {
    iv_clear(dst);
    for (int i = 0; i < src->n; i++) iv_push(dst, src->a[i], src->b[i]);
}

/* ================================================================== */
/* Curve                                                               */
/* ================================================================== */

void curve_init(Curve *c) { c->n = c->cap = 0; c->ts = c->ls = c->rs = NULL; }
void curve_free(Curve *c) { free(c->ts); free(c->ls); free(c->rs); curve_init(c); }

void curve_push(Curve *c, Rat t, Rat l, Rat r) {
    if (c->n == c->cap) {
        c->cap = c->cap ? c->cap * 2 : 8;
        c->ts = xrealloc(c->ts, sizeof(Rat) * c->cap);
        c->ls = xrealloc(c->ls, sizeof(Rat) * c->cap);
        c->rs = xrealloc(c->rs, sizeof(Rat) * c->cap);
    }
    c->ts[c->n] = t;
    c->ls[c->n] = l;
    c->rs[c->n] = r;
    c->n++;
}

/* 第一個 >= t 的位置（Python 的 bisect_left） */
static int bisect_left(const Curve *c, Rat t) {
    int lo = 0, hi = c->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (rlt(c->ts[mid], t)) lo = mid + 1; else hi = mid;
    }
    return lo;
}

/* 第一個 > t 的位置（Python 的 bisect_right） */
static int bisect_right(const Curve *c, Rat t) {
    int lo = 0, hi = c->n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (rle(c->ts[mid], t)) lo = mid + 1; else hi = mid;
    }
    return lo;
}

/* t 落在 ts[i-1] 與 ts[i] 之間：從前一點的 rs 直線內插到後一點的 ls */
static Rat between_value(const Curve *c, int i, Rat t) {
    Rat x0 = c->ts[i - 1], y0 = c->rs[i - 1], x1 = c->ts[i], y1 = c->ls[i];
    /* y0 + (y1 - y0) * (t - x0) / (x1 - x0) */
    return radd(y0, rdiv(rmul(rsub(y1, y0), rsub(t, x0)), rsub(x1, x0)));
}

/* t 的左極限（剛到 t 之前的值） */
Rat curve_left(const Curve *c, Rat t) {
    if (c->n == 0) return R(0);                     /* 空曲線：沒有占用 */
    int i = bisect_left(c, t);
    if (i == c->n) return c->rs[c->n - 1];          /* 最後一點之後：維持最後的值 */
    if (req(c->ts[i], t) || i == 0) return c->ls[i];/* 剛好是變化點，或在第一點之前 */
    return between_value(c, i, t);                  /* 兩點之間：內插 */
}

/* t 的右極限（剛過 t 之後的值） */
Rat curve_right(const Curve *c, Rat t) {
    if (c->n == 0) return R(0);
    int i = bisect_left(c, t);
    if (i == c->n) return c->rs[c->n - 1];
    if (req(c->ts[i], t)) return c->rs[i];          /* 剛好是變化點：取右極限 */
    if (i == 0) return c->ls[0];
    return between_value(c, i, t);
}

/* 左右極限取大的，保守地當作這一刻的占用 */
Rat curve_top(const Curve *c, Rat t) {
    return rmax(curve_left(c, t), curve_right(c, t));
}

/* 嚴格落在 (a, b) 內的變化點：ts[first .. first+回傳值-1] */
int curve_between(const Curve *c, Rat a, Rat b, int *first) {
    *first = 0;
    if (!rlt(a, b)) return 0;
    int i = bisect_right(c, a), j = bisect_left(c, b);
    *first = i;
    return j > i ? j - i : 0;
}

/* [a, b] 內的最高占用：兩端加上中間的變化點（直線的最大值在端點） */
Rat curve_peak(const Curve *c, Rat a, Rat b) {
    Rat best = rmax(curve_top(c, a), curve_top(c, b));
    int first, k = curve_between(c, a, b, &first);
    for (int i = first; i < first + k; i++) best = rmax(best, curve_top(c, c->ts[i]));
    return best;
}

/*
 * dst = dst + o。
 * 變化點取聯集，每點 ls 加 ls、rs 加 rs，
 * 最後刪掉「沒有跳變、而且落在前後兩點連線上」的點（Python 的 _prune）。
 */
void curve_add(Curve *dst, const Curve *o) {
    /* 1. 合併兩邊的 ts（都已排序），去掉重複 */
    int na = dst->n, nb = o->n, n = 0;
    Rat *ts = malloc(sizeof(Rat) * (na + nb + 1));
    int i = 0, j = 0;
    while (i < na || j < nb) {
        Rat t;
        if (j >= nb || (i < na && rlt(dst->ts[i], o->ts[j]))) t = dst->ts[i++];
        else if (i >= na || rlt(o->ts[j], dst->ts[i])) t = o->ts[j++];
        else { t = dst->ts[i++]; j++; }
        ts[n++] = t;
    }
    /* 2. 每點左右極限各自相加 */
    Rat *ls = malloc(sizeof(Rat) * (n + 1)), *rs = malloc(sizeof(Rat) * (n + 1));
    for (int k = 0; k < n; k++) {
        ls[k] = radd(curve_left(dst, ts[k]), curve_left(o, ts[k]));
        rs[k] = radd(curve_right(dst, ts[k]), curve_right(o, ts[k]));
    }
    /* 3. 刪掉共線的多餘點 */
    Curve out;
    curve_init(&out);
    if (n < 3) {
        for (int k = 0; k < n; k++) curve_push(&out, ts[k], ls[k], rs[k]);
    } else {
        curve_push(&out, ts[0], ls[0], rs[0]);
        for (int k = 1; k < n - 1; k++) {
            if (req(ls[k], rs[k])) {                 /* 這點沒有跳變 */
                Rat x0 = out.ts[out.n - 1], y0 = out.rs[out.n - 1];
                Rat x1 = ts[k + 1], y1 = ls[k + 1];
                /* 三點共線：(ls[k] − y0)(x1 − x0) == (y1 − y0)(ts[k] − x0) */
                if (req(rmul(rsub(ls[k], y0), rsub(x1, x0)), rmul(rsub(y1, y0), rsub(ts[k], x0))))
                    continue;
            }
            curve_push(&out, ts[k], ls[k], rs[k]);
        }
        curve_push(&out, ts[n - 1], ls[n - 1], rs[n - 1]);
    }
    free(ts); free(ls); free(rs);
    curve_free(dst);
    *dst = out;
}

/* ================================================================== */
/* 小工具                                                              */
/* ================================================================== */

/* 從 a 到 b 由 0 直線升到 S：t 時刻「已經傳了多少」 */
Rat ramp(Rat t, Rat a, Rat b, Rat S) {
    if (rle(t, a)) return R(0);
    if (rge(t, b)) return S;
    return rdiv(rmul(S, rsub(t, a)), rsub(b, a));
}

/*
 * 前一跳出發到下一跳最早出發的間隔（不含傳播延遲）。
 *   收完才轉：S / r1
 *   邊收邊轉：max(0, S/r1 − S/r2)
 */
Rat lag(const Problem *P, const Contact *c1, const Contact *c2) {
    Rat d1 = rdiv(P->S, c1->r), d2 = rdiv(P->S, c2->r);
    return P->ct ? rmax(R(0), rsub(d1, d2)) : d1;
}

/* 到達時間 = 最後一跳出發 + 傳輸時間 + 傳播延遲 */
Rat arrival(const Problem *P, const Schedule *sch) {
    const Contact *c = &P->cs[sch->c[sch->n - 1]];
    return radd(radd(sch->s[sch->n - 1], rdiv(P->S, c->r)), c->d);
}

void sched_free(Schedule *s) { free(s->c); free(s->s); s->c = NULL; s->s = NULL; s->n = 0; }
