/*
 * search.c：本方法的搜尋。對應 Python 的 ours.py（文件 Algorithm 2～6）。
 *
 * 一包的處理流程：
 *   plan
 *     search                 找到最早到達目的地的 Label
 *       candidate_range      連線開放時間、期限、扣掉預約 → 可出發區間
 *       source_filter        來源的 Buffer
 *       buffer_filter        中繼的 Buffer
 *       destination_filter   目的地的 Buffer
 *         solve_region       細緻檢查（三個 filter 共用）
 *       insert               去重後放進優先佇列
 *     backtrack              從終點回推每一跳的出發時間
 */
#include <string.h>
#include "dtn.h"

/* ================================================================== */
/* 區間運算                                                            */
/* ================================================================== */

/* 從閉區間清單 in 扣掉開區間 (x, y)，結果放 out。
 * 例：[(105, 150)] 扣掉 (110, 130) → [(105, 110), (130, 150)] */
void subtract_open(const IvList *in, Rat x, Rat y, IvList *out) {
    iv_clear(out);
    for (int i = 0; i < in->n; i++) {
        Rat a = in->a[i], b = in->b[i];
        if (rle(y, a) || rge(x, b)) { iv_push(out, a, b); continue; }  /* 沒重疊 */
        if (rle(a, x)) iv_push(out, a, x);                            /* 左邊剩一段 */
        if (rle(y, b)) iv_push(out, y, b);                            /* 右邊剩一段 */
    }
}

/* 從 parts 扣掉已經到過的 done（done 已排序、不重疊），結果放 out。
 * 例：done [(100, 130)]、parts [(120, 140)] → [(130, 140)] */
void minus(const IvList *parts, const IvList *done, IvList *out) {
    iv_clear(out);
    for (int i = 0; i < parts->n; i++) {
        Rat a = parts->a[i], b = parts->b[i];
        Rat cur = a;
        int closed = 0;
        for (int j = 0; j < done->n; j++) {
            Rat x = done->a[j], y = done->b[j];
            if (rlt(y, cur)) continue;
            if (rgt(x, b)) break;
            if (rgt(x, cur)) iv_push(out, cur, x);
            cur = rmax(cur, y);
            closed = 1;
            if (rge(cur, b)) break;
        }
        if (rlt(cur, b) || (req(cur, b) && !closed)) iv_push(out, cur, b);
    }
}

/* 依 (a, b) 排序，把重疊或相接的區間合併（原地修改）。
 * 例：[(110, 120), (100, 110)] → [(100, 120)] */
void merge(IvList *v) {
    /* 插入排序：區間數通常很少 */
    for (int i = 1; i < v->n; i++) {
        for (int j = i; j > 0; j--) {
            int c = rcmp(v->a[j], v->a[j - 1]);
            if (c > 0 || (c == 0 && rge(v->b[j], v->b[j - 1]))) break;
            Rat ta = v->a[j], tb = v->b[j];
            v->a[j] = v->a[j - 1]; v->b[j] = v->b[j - 1];
            v->a[j - 1] = ta; v->b[j - 1] = tb;
        }
    }
    int n = 0;
    for (int i = 0; i < v->n; i++) {
        if (n > 0 && rle(v->a[i], v->b[n - 1])) {
            v->b[n - 1] = rmax(v->b[n - 1], v->b[i]);
        } else {
            v->a[n] = v->a[i]; v->b[n] = v->b[i]; n++;
        }
    }
    v->n = n;
}

/* ================================================================== */
/* 第一關：連線限制（Algorithm 3）                                       */
/*   lo = max(連線開始, head)                                          */
/*   hi = min(連線結束 − d, 期限 − d − 延遲)                            */
/*   對每筆預約 (x, y) 扣掉開區間 (x − d, y)                             */
/* ================================================================== */
void candidate_range(const Problem *P, const Contact *c, Rat head, IvList *out) {
    iv_clear(out);
    Rat d = rdiv(P->S, c->r);
    Rat lo = rmax(c->a, head);
    Rat hi = rmin(rsub(c->b, d), rsub(rsub(P->T, d), c->d));
    if (rgt(lo, hi)) return;
    iv_push(out, lo, hi);
    IvList tmp;
    iv_init(&tmp);
    for (int i = 0; i < c->F.n; i++) {
        subtract_open(out, rsub(c->F.a[i], d), c->F.b[i], &tmp);
        iv_copy(out, &tmp);
    }
    iv_free(&tmp);
}

/* ================================================================== */
/* 細緻檢查（三個 filter 共用）                                          */
/*                                                                    */
/* 在 [lo, hi] 找出所有可行的出發時間 s：                                 */
/*  1. 用切點 bps 把 [lo, hi] 切成好幾段。                                */
/*  2. 每個切點用 feas 直接檢查（切點上可能有跳變，要用原規則）。              */
/*  3. 每段內，每個檢查點的合計水位都是 s 的一次式：                         */
/*     在 1/3 點 e、2/3 點 g 各算一次，得到斜率 k。                         */
/*  4. 解 v(e) + k (s − e) ≤ M：k > 0 得上界，k < 0 得下界，                */
/*     k = 0 時值超過 M 就整段不行。                                      */
/*  5. 合併可行的點與小段，附加到 out。                                    */
/*                                                                    */
/* Python 版用 lambda 傳 feas、vals；C 用函式指標加上一個 ctx 指標。         */
/* vals(ctx, s, m, buf) 把各檢查點的合計水位寫進 buf，回傳個數；             */
/* m 是段中點，用來決定這段內哪些舊變化點落在停留期間。                      */
/* ================================================================== */
typedef int (*FeasFn)(void *ctx, Rat s);
typedef int (*ValsFn)(void *ctx, Rat s, Rat m, Rat *buf);

static void solve_region(const Problem *P, Rat lo, Rat hi, const Rat *bps, int nb,
                         void *ctx, FeasFn feas, ValsFn vals, int cap, IvList *out) {
    /* 1. 切點：lo、hi 加上落在 (lo, hi) 內的 bps，排序去重 */
    Rat *pts = malloc(sizeof(Rat) * (nb + 2));
    int np = 0;
    pts[np++] = lo;
    if (!req(lo, hi)) pts[np++] = hi;
    for (int i = 0; i < nb; i++) {
        if (!(rlt(lo, bps[i]) && rlt(bps[i], hi))) continue;
        int dup = 0;
        for (int j = 0; j < np; j++) if (req(pts[j], bps[i])) { dup = 1; break; }
        if (!dup) pts[np++] = bps[i];
    }
    for (int i = 1; i < np; i++)
        for (int j = i; j > 0 && rlt(pts[j], pts[j - 1]); j--) { Rat t = pts[j]; pts[j] = pts[j - 1]; pts[j - 1] = t; }

    IvList res;
    iv_init(&res);
    /* 2. 切點本身 */
    for (int i = 0; i < np; i++)
        if (feas(ctx, pts[i])) iv_push(&res, pts[i], pts[i]);

    /* 3～4. 每一段 (p, q) */
    Rat *va = malloc(sizeof(Rat) * cap), *vb = malloc(sizeof(Rat) * cap);
    for (int i = 0; i + 1 < np; i++) {
        Rat p = pts[i], q = pts[i + 1], w = rsub(q, p);
        Rat e = radd(p, rdiv(w, R(3)));
        Rat g = radd(p, rdiv(rmul(w, R(2)), R(3)));
        Rat m = rdiv(radd(p, q), R(2));
        int na = vals(ctx, e, m, va);
        int nbv = vals(ctx, g, m, vb);
        if (na != nbv) { fprintf(stderr, "solve_region: 檢查點數不一致\n"); exit(2); }
        Rat L = p, H = q;
        int ok = 1;
        for (int k = 0; k < na; k++) {
            Rat slope = rdiv(rsub(vb[k], va[k]), rsub(g, e));       /* 斜率 */
            int sg = rcmp(slope, R(0));
            if (sg == 0) {
                if (rgt(va[k], P->M)) { ok = 0; break; }
            } else {
                Rat bound = radd(e, rdiv(rsub(P->M, va[k]), slope));  /* e + (M − v(e)) / k */
                if (sg > 0) H = rmin(H, bound);                         /* 上界 */
                else L = rmax(L, bound);                                /* 下界 */
            }
        }
        if (ok && rle(L, H)) iv_push(&res, L, H);
    }
    /* 5. 合併後附加 */
    merge(&res);
    for (int i = 0; i < res.n; i++) iv_push(out, res.a[i], res.b[i]);
    iv_free(&res);
    free(pts); free(va); free(vb);
}

/* ================================================================== */
/* 第二關：Buffer 篩選。每個都是「先快速檢查，不行再細緻檢查」               */
/* 快速檢查：peak(視窗) + S ≤ M。視窗是這包在該節點最多可能停留的範圍；       */
/* 整包一直疊在最高點都不爆，任何出發時間就都不爆，整段保留。                  */
/* ================================================================== */

/* ---------- 來源：g 起整包占著，s 開始送 ---------- */
typedef struct {
    const Problem *P;
    const Contact *c;
    const Curve *O;
    Rat d;
} SrcCtx;

static int src_feas(void *p, Rat s) {
    SrcCtx *x = p;
    return source_ok(x->P, x->c, s);
}

static int src_vals(void *p, Rat s, Rat m, Rat *buf) {
    SrcCtx *x = p;
    const Problem *P = x->P;
    int n = 0;
    buf[n++] = radd(curve_right(x->O, P->g), P->S);     /* g：整包在 */
    buf[n++] = radd(curve_top(x->O, s), P->S);          /* s：開始送，整包還在 */
    int first, k = curve_between(x->O, P->g, radd(m, x->d), &first);
    for (int i = first; i < first + k; i++) {           /* 送出中 */
        Rat t = x->O->ts[i];
        buf[n++] = rsub(radd(curve_top(x->O, t), P->S), ramp(t, s, radd(s, x->d), P->S));
    }
    return n;
}

static void source_filter(const Problem *P, const Contact *c, const IvList *parts, IvList *out) {
    iv_clear(out);
    const Curve *O = &P->O[P->src];
    Rat d = rdiv(P->S, c->r);
    for (int i = 0; i < parts->n; i++) {
        Rat lo = parts->a[i], hi = parts->b[i];
        if (rle(radd(curve_peak(O, P->g, radd(hi, d)), P->S), P->M)) {   /* 快速檢查 */
            iv_push(out, lo, hi);
            continue;
        }
        /* 切點：s 碰到舊變化點 x（開始送），或 s + d 碰到 x（送完） */
        int first, k = curve_between(O, P->g, radd(hi, d), &first);
        Rat *bps = malloc(sizeof(Rat) * (2 * k + 1));
        int nb = 0;
        for (int j = first; j < first + k; j++) bps[nb++] = O->ts[j];
        for (int j = first; j < first + k; j++) bps[nb++] = rsub(O->ts[j], d);
        SrcCtx ctx = { P, c, O, d };
        solve_region(P, lo, hi, bps, nb, &ctx, src_feas, src_vals, O->n + 3, out);
        free(bps);
    }
}

/* ---------- 目的地：只收不送，A 交付 ---------- */
typedef struct {
    const Problem *P;
    const Contact *c;
    const Curve *O;
    Rat d;
} DstCtx;

static int dst_feas(void *p, Rat s) {
    DstCtx *x = p;
    return destination_ok(x->P, x->c, s);
}

static int dst_vals(void *p, Rat s, Rat m, Rat *buf) {
    DstCtx *x = p;
    const Problem *P = x->P;
    Rat h = radd(s, x->c->d), A = radd(h, x->d);        /* 開始收、收完 */
    int n = 0;
    buf[n++] = radd(curve_left(x->O, A), P->S);         /* 收完前一瞬間：整包 */
    Rat a = radd(m, x->c->d);
    int first, k = curve_between(x->O, a, radd(a, x->d), &first);
    for (int i = first; i < first + k; i++) {           /* 收的過程中 */
        Rat t = x->O->ts[i];
        buf[n++] = radd(curve_top(x->O, t), ramp(t, h, A, P->S));
    }
    return n;
}

static void destination_filter(const Problem *P, const Contact *c, const IvList *parts, IvList *out) {
    iv_clear(out);
    const Curve *O = &P->O[P->dst];
    if (O->n == 0) {                                    /* 目的地完全沒有占用 */
        if (rle(P->S, P->M)) iv_copy(out, parts);
        return;
    }
    Rat d = rdiv(P->S, c->r);
    for (int i = 0; i < parts->n; i++) {
        Rat lo = parts->a[i], hi = parts->b[i];
        Rat wa = radd(lo, c->d), wb = radd(radd(hi, c->d), d);
        if (rle(radd(curve_peak(O, wa, wb), P->S), P->M)) {             /* 快速檢查 */
            iv_push(out, lo, hi);
            continue;
        }
        /* 切點：開始收 h 或收完 A 碰到舊變化點 x */
        int first, k = curve_between(O, wa, wb, &first);
        Rat *bps = malloc(sizeof(Rat) * (2 * k + 1));
        int nb = 0;
        for (int j = first; j < first + k; j++) bps[nb++] = rsub(O->ts[j], c->d);
        for (int j = first; j < first + k; j++) bps[nb++] = rsub(rsub(O->ts[j], c->d), d);
        DstCtx ctx = { P, c, O, d };
        solve_region(P, lo, hi, bps, nb, &ctx, dst_feas, dst_vals, O->n + 3, out);
        free(bps);
    }
}

/* ---------- 中繼（Algorithm 4） ----------
 * 變數是下一跳 c2 的出發時間 s2。
 * 對每個 s2，前一跳只試最晚的 s1* = min(L1.hi, s2 − dl − lag)：
 *   s2 固定時 s1 越晚，在中繼停留越短；最晚的不行，更早的也不會行。
 *   s1* < L1.lo 表示前一跳趕不上。
 */
typedef struct {
    const Problem *P;
    const Contact *c1, *c2;
    Rat L1lo, L1hi;
    const Curve *O;
    Rat d1, d2, dl, gap;
} RelCtx;

/* s2 = s 時的 s1*；趕不上回傳 0 */
static int rel_star(const RelCtx *x, Rat s, Rat *k) {
    Rat u = rsub(rsub(s, x->dl), x->gap);
    if (rlt(u, x->L1lo)) return 0;
    *k = rmin(x->L1hi, u);
    return 1;
}

static int rel_feas(void *p, Rat s) {
    RelCtx *x = p;
    Rat k;
    return rel_star(x, s, &k) && relay_ok(x->P, x->c1, k, x->c2, s);
}

/* 這包在中繼的量：已收 − 已送 */
static Rat rel_own(Rat t, Rat h, Rat A, Rat s, Rat f, Rat S) {
    return rsub(ramp(t, h, A, S), ramp(t, s, f, S));
}

static int rel_vals(void *p, Rat s, Rat m, Rat *buf) {
    RelCtx *x = p;
    Rat S = x->P->S, k, km;
    rel_star(x, s, &k);   /* 段內一定趕得上：候選區間的 lo ≥ L1.lo + dl + lag */
    rel_star(x, m, &km);
    Rat h = radd(k, x->dl), A = radd(h, x->d1), f = radd(s, x->d2);   /* 開始收、收完、送完 */
    Rat hm = radd(km, x->dl);
    int n = 0;
    buf[n++] = radd(curve_top(x->O, A), rel_own(A, h, A, s, f, S));   /* 收完 */
    buf[n++] = radd(curve_top(x->O, s), rel_own(s, h, A, s, f, S));   /* 開始送 */
    int first, c = curve_between(x->O, hm, radd(m, x->d2), &first);
    for (int i = first; i < first + c; i++) {                          /* 停留期間的舊變化點 */
        Rat t = x->O->ts[i];
        buf[n++] = radd(curve_top(x->O, t), rel_own(t, h, A, s, f, S));
    }
    return n;
}

static void buffer_filter(const Problem *P, const IvList *parts, int c1i, Rat L1lo, Rat L1hi,
                          const Contact *c2, IvList *out) {
    iv_clear(out);
    const Contact *c1 = &P->cs[c1i];
    const Curve *O = &P->O[c1->v];                       /* 中繼節點的占用 */
    Rat d1 = rdiv(P->S, c1->r), d2 = rdiv(P->S, c2->r), dl = c1->d;
    Rat gap = lag(P, c1, c2);
    Rat clamp = radd(radd(L1hi, dl), gap);               /* s2 超過這裡，s1* 被 L1.hi 卡住 */
    RelCtx ctx = { P, c1, c2, L1lo, L1hi, O, d1, d2, dl, gap };
    for (int i = 0; i < parts->n; i++) {
        Rat lo = parts->a[i], hi = parts->b[i];
        Rat wa = radd(L1lo, dl), wb = radd(hi, d2);      /* 視窗：最早開始收 ～ 最晚送完 */
        if (rle(radd(curve_peak(O, wa, wb), P->S), P->M)) {             /* 快速檢查 */
            iv_push(out, lo, hi);
            continue;
        }
        /* 切點：新包的 h = s − gap、A = s − gap + d1、s、f = s + d2 碰到 O 的變化點 x；
         * clamp 之後 h、A 固定；邊收邊轉時 s 越過固定的 A，own(A)、own(s) 會折彎 */
        int first, k = curve_between(O, wa, wb, &first);
        Rat *bps = malloc(sizeof(Rat) * (4 * k + 2));
        int nb = 0;
        bps[nb++] = clamp;
        bps[nb++] = radd(radd(L1hi, dl), d1);
        for (int j = first; j < first + k; j++) {
            Rat x = O->ts[j];
            bps[nb++] = x;
            bps[nb++] = rsub(x, d2);
            bps[nb++] = radd(x, gap);
            bps[nb++] = rsub(radd(x, gap), d1);
        }
        solve_region(P, lo, hi, bps, nb, &ctx, rel_feas, rel_vals, O->n + 3, out);
        free(bps);
    }
    merge(out);
}

/* ================================================================== */
/* 搜尋（Algorithm 2）                                                  */
/* 像 Dijkstra 一樣用優先佇列，每次取出「最早到達」的 Label；                */
/* 第一個取出、到達目的地的 Label 就是最早到達。                            */
/* 路徑不重複經過同一節點；去重仍以連線為單位。                                    */
/* ================================================================== */

typedef struct {
    int c;          /* 走哪條連線 */
    Rat lo, hi;     /* 可出發區間 */
    int pred;       /* 前一跳 Label 的編號，-1 表示第一跳 */
} Label;

typedef struct {
    Rat key;            /* 以最早出發計算的到達時間 */
    long long tick;     /* 同分時維持放入順序 */
    int lab;
} HeapItem;

typedef struct {
    Label *lab; int nl, capl;        /* 所有 Label */
    HeapItem *h; int nh, caph;       /* 優先佇列（二元堆積） */
    IvList *reached;                 /* 每條連線已放過的出發區間 */
    long long tick;
} Search;

static int heap_less(const HeapItem *a, const HeapItem *b) {
    int c = rcmp(a->key, b->key);
    return c < 0 || (c == 0 && a->tick < b->tick);
}

static void heap_push(Search *S, HeapItem it) {
    if (S->nh == S->caph) {
        S->caph = S->caph ? S->caph * 2 : 64;
        S->h = realloc(S->h, sizeof(HeapItem) * S->caph);
    }
    int i = S->nh++;
    S->h[i] = it;
    while (i > 0) {                                  /* 往上浮 */
        int p = (i - 1) / 2;
        if (!heap_less(&S->h[i], &S->h[p])) break;
        HeapItem t = S->h[i]; S->h[i] = S->h[p]; S->h[p] = t;
        i = p;
    }
}

static HeapItem heap_pop(Search *S) {
    HeapItem top = S->h[0];
    S->h[0] = S->h[--S->nh];
    int i = 0;
    for (;;) {                                       /* 往下沉 */
        int l = 2 * i + 1, r = l + 1, m = i;
        if (l < S->nh && heap_less(&S->h[l], &S->h[m])) m = l;
        if (r < S->nh && heap_less(&S->h[r], &S->h[m])) m = r;
        if (m == i) break;
        HeapItem t = S->h[i]; S->h[i] = S->h[m]; S->h[m] = t;
        i = m;
    }
    return top;
}

/* 去重後把新的 Label 放進佇列：只保留這條連線還沒放過的出發區間 */
static void insert(const Problem *P, Search *S, int c, const IvList *parts, int pred) {
    IvList *done = &S->reached[c], fresh;
    iv_init(&fresh);
    minus(parts, done, &fresh);
    merge(&fresh);
    if (fresh.n == 0) { iv_free(&fresh); return; }
    for (int i = 0; i < fresh.n; i++) iv_push(done, fresh.a[i], fresh.b[i]);
    merge(done);
    const Contact *ct = &P->cs[c];
    for (int i = 0; i < fresh.n; i++) {
        if (S->nl == S->capl) {
            S->capl = S->capl ? S->capl * 2 : 64;
            S->lab = realloc(S->lab, sizeof(Label) * S->capl);
        }
        Label L = { c, fresh.a[i], fresh.b[i], pred };
        S->lab[S->nl] = L;
        HeapItem it = { radd(radd(fresh.a[i], rdiv(P->S, ct->r)), ct->d), ++S->tick, S->nl };
        S->nl++;
        heap_push(S, it);
    }
    iv_free(&fresh);
}

/* 節點 node 是否已在 Label lab 的路徑上（來源，加上每一跳的終點） */
static int on_path(const Problem *P, const Search *S, int lab, int node) {
    if (node == P->src) return 1;
    for (int i = lab; i >= 0; i = S->lab[i].pred)
        if (P->cs[S->lab[i].c].v == node) return 1;
    return 0;
}

/* 回傳到達目的地的 Label 編號，找不到回傳 -1。結果留在 S 裡給 backtrack 用。
 * 路徑不重複經過同一節點（2026-11-23 使用者決定）。 */
static int search(const Problem *P, Search *S) {
    if (rgt(P->S, P->M)) return -1;                 /* 包比 Buffer 還大 */

    IvList a, b;
    iv_init(&a); iv_init(&b);

    /* 第一跳：從來源出去的每條連線（依連線順序） */
    for (int c = 0; c < P->nc; c++) {
        const Contact *ct = &P->cs[c];
        if (ct->u != P->src) continue;
        candidate_range(P, ct, P->g, &a);
        source_filter(P, ct, &a, &b);
        if (ct->v == P->dst) {                       /* 一跳就到 */
            destination_filter(P, ct, &b, &a);
            iv_copy(&b, &a);
        }
        insert(P, S, c, &b, -1);
    }

    int goal = -1;
    while (S->nh > 0) {
        HeapItem it = heap_pop(S);
        Label L1 = S->lab[it.lab];
        const Contact *c1 = &P->cs[L1.c];
        if (c1->v == P->dst) { goal = it.lab; break; }   /* 已到目的地：這就是最早的 */
        /* 往下一跳展開：從 L1 到達的節點出去的每條連線 */
        for (int c = 0; c < P->nc; c++) {
            const Contact *c2 = &P->cs[c];
            if (c2->u != c1->v) continue;
            if (on_path(P, S, it.lab, c2->v)) continue;   /* 不重複經過同一節點 */
            Rat head = radd(radd(L1.lo, c1->d), lag(P, c1, c2));   /* 下一跳最早可出發 */
            candidate_range(P, c2, head, &a);
            if (a.n == 0) continue;
            buffer_filter(P, &a, L1.c, L1.lo, L1.hi, c2, &b);
            if (c2->v == P->dst) {
                destination_filter(P, c2, &b, &a);
                iv_copy(&b, &a);
            }
            insert(P, S, c, &b, it.lab);
        }
    }
    iv_free(&a); iv_free(&b);
    return goal;
}

/* ================================================================== */
/* 回推（Algorithm 6）與對外介面                                         */
/* 最後一跳取最早（lo）；往前每一跳取「趕得上下一跳的最晚出發」：             */
/*   k = min(前一跳 hi, 下一跳出發 − 延遲 − lag)                          */
/* ================================================================== */
static void backtrack(const Problem *P, const Search *S, int goal, Schedule *out) {
    int n = 0;
    for (int i = goal; i >= 0; i = S->lab[i].pred) n++;
    out->n = n;
    out->c = malloc(sizeof(int) * n);
    out->s = malloc(sizeof(Rat) * n);
    int i = goal, pos = n - 1;
    Rat s = S->lab[goal].lo;
    out->c[pos] = S->lab[i].c;
    out->s[pos] = s;
    while (S->lab[i].pred >= 0) {
        const Label *q = &S->lab[S->lab[i].pred];
        const Contact *qc = &P->cs[q->c], *nc = &P->cs[S->lab[i].c];
        Rat k = rmin(q->hi, rsub(rsub(s, qc->d), lag(P, qc, nc)));
        pos--;
        out->c[pos] = q->c;
        out->s[pos] = k;
        i = S->lab[i].pred;
        s = k;
    }
}

int plan(const Problem *P, Schedule *out) {
    Search S;
    memset(&S, 0, sizeof S);
    S.reached = calloc(P->nc, sizeof(IvList));
    int goal = search(P, &S);
    if (goal >= 0) backtrack(P, &S, goal, out);
    for (int c = 0; c < P->nc; c++) iv_free(&S.reached[c]);
    free(S.reached); free(S.lab); free(S.h);
    return goal >= 0;
}
