/*
 * rules.c：規則本身與寫入。對應 Python 的 validate.py。
 *
 * 這個檔案不呼叫任何搜尋函式。用途：
 *   1. 搜尋找到排程後，用這裡的規則獨立回放檢查。
 *   2. 搜尋的細緻檢查在「切點」上直接用這裡的 *_ok 判斷。
 *
 * 中繼節點的符號：
 *   h = s1 + d1（開始收）、A = h + S/r1（收完）、f = s2 + S/r2（送完）
 */
#include "dtn.h"

/* ================================================================== */
/* 這一包在某節點的量 own(t)                                            */
/*                                                                    */
/* 三種節點都可以寫成：own(t) = base + Σ sign[k] × ramp(t, a[k], b[k], S) */
/*   來源：S − ramp(t, s, f)                                          */
/*   中繼：ramp(t, h, A) − ramp(t, s2, f)                              */
/*   目的地：ramp(t, h, A)                                             */
/* Python 版用 lambda，C 用這個小結構代替。                               */
/* ================================================================== */
typedef struct {
    Rat S, base;
    int k;          /* 有幾個 ramp（1 或 2） */
    Rat a[2], b[2];
    int sign[2];    /* +1 或 -1 */
} Own;

static Rat own_at(const Own *w, Rat t) {
    Rat v = w->base;
    for (int i = 0; i < w->k; i++) {
        Rat r = ramp(t, w->a[i], w->b[i], w->S);
        v = w->sign[i] > 0 ? radd(v, r) : rsub(v, r);
    }
    return v;
}

/* ================================================================== */
/* Buffer 檢查核心：start 到 end 之間每一刻 O(t) + own(t) ≤ M            */
/*                                                                    */
/* 只檢查：起點（O 的右極限）、終點（O 的左極限）、                        */
/*        這包自己的變化點 pts、O 在 (start, end) 內的變化點。             */
/* 已知限制：own 為 0 的時刻不檢查（背景本身超過 M 時才有影響）。             */
/* ================================================================== */
static int stay_ok(const Curve *O, Rat M, Rat start, Rat end,
                   const Own *own, Rat own_end, const Rat *pts, int npts) {
    Rat v = own_at(own, start);
    if (rgt(v, R(0)) && rgt(radd(curve_right(O, start), v), M)) return 0;
    if (rgt(own_end, R(0)) && rgt(radd(curve_left(O, end), own_end), M)) return 0;
    for (int i = 0; i < npts; i++) {                     /* 這包自己的變化點 */
        Rat t = pts[i];
        if (rlt(start, t) && rlt(t, end)) {
            v = own_at(own, t);
            if (rgt(v, R(0)) && rgt(radd(curve_top(O, t), v), M)) return 0;
        }
    }
    int first, k = curve_between(O, start, end, &first); /* O 的變化點 */
    for (int i = first; i < first + k; i++) {
        Rat t = O->ts[i];
        v = own_at(own, t);
        if (rgt(v, R(0)) && rgt(radd(curve_top(O, t), v), M)) return 0;
    }
    return 1;
}

/* ================================================================== */
/* 三種節點的 Buffer 規則                                               */
/* ================================================================== */

/* 來源：g 起整包占著，s 開始送、f = s + S/r 送完 */
int source_ok(const Problem *P, const Contact *c, Rat s) {
    Rat f = radd(s, rdiv(P->S, c->r));
    Own w = { P->S, P->S, 1, { s }, { f }, { -1 } };    /* S − ramp(t, s, f) */
    Rat pts[1] = { s };
    return stay_ok(&P->O[P->src], P->M, P->g, f, &w, R(0), pts, 1);
}

/* 中繼：先檢查轉送條件，再檢查 Buffer */
int relay_ok(const Problem *P, const Contact *c1, Rat s1, const Contact *c2, Rat s2) {
    Rat h = radd(s1, c1->d);                     /* 開始收 */
    Rat A = radd(h, rdiv(P->S, c1->r));          /* 收完 */
    Rat f = radd(s2, rdiv(P->S, c2->r));         /* 送完 */
    if (P->ct) {
        if (rlt(s2, h) || rlt(f, A)) return 0;  /* 邊收邊轉：已開始收，且送不能比收快 */
    } else if (rlt(s2, A)) {
        return 0;                                /* 收完才轉：收完才送 */
    }
    Own w = { P->S, R(0), 2, { h, s2 }, { A, f }, { +1, -1 } };   /* 已收 − 已送 */
    Rat pts[2] = { A, s2 };
    return stay_ok(&P->O[c1->v], P->M, h, f, &w, R(0), pts, 2);
}

/* 目的地：只收不送，A（收完）那一刻交付歸零 */
int destination_ok(const Problem *P, const Contact *c, Rat s) {
    Rat h = radd(s, c->d);
    Rat A = radd(h, rdiv(P->S, c->r));
    Own w = { P->S, R(0), 1, { h }, { A }, { +1 } };
    /* own_end = S：A 的左極限是整包（交付前一瞬間還在） */
    return stay_ok(&P->O[P->dst], P->M, h, A, &w, P->S, NULL, 0);
}

/* ================================================================== */
/* 連線規則                                                            */
/* ================================================================== */

/* s ≥ 連線開始；傳得完；期限前到；不和預約 (x, y) 重疊（s < y 且 x < s + d） */
int hop_ok(const Problem *P, const Contact *c, Rat s) {
    Rat d = rdiv(P->S, c->r);
    Rat end = radd(s, d);
    if (rlt(s, c->a) || rgt(end, c->b) || rgt(radd(end, c->d), P->T)) return 0;
    for (int i = 0; i < c->F.n; i++)
        if (rlt(s, c->F.b[i]) && rlt(c->F.a[i], end)) return 0;
    return 1;
}

/* ================================================================== */
/* 整條排程的檢查                                                       */
/* ================================================================== */
int validate(const Problem *P, const Schedule *sch) {
    if (sch->n == 0) return 0;
    const Contact *first = &P->cs[sch->c[0]], *last = &P->cs[sch->c[sch->n - 1]];
    if (first->u != P->src || last->v != P->dst || rlt(sch->s[0], P->g)) return 0;
    for (int i = 0; i + 1 < sch->n; i++)                     /* 接得起來 */
        if (P->cs[sch->c[i]].v != P->cs[sch->c[i + 1]].u) return 0;
    for (int i = 0; i < sch->n; i++) {                       /* 不重複經過同一節點 */
        int v = P->cs[sch->c[i]].v;
        if (v == P->src) return 0;
        for (int j = 0; j < i; j++) if (P->cs[sch->c[j]].v == v) return 0;
    }
    for (int i = 0; i < sch->n; i++)                         /* 每一跳 */
        if (!hop_ok(P, &P->cs[sch->c[i]], sch->s[i])) return 0;
    if (!source_ok(P, first, sch->s[0])) return 0;
    if (!destination_ok(P, last, sch->s[sch->n - 1])) return 0;
    for (int i = 0; i + 1 < sch->n; i++)                     /* 每個中繼 */
        if (!relay_ok(P, &P->cs[sch->c[i]], sch->s[i], &P->cs[sch->c[i + 1]], sch->s[i + 1])) return 0;
    return 1;
}

/* ================================================================== */
/* 排定後寫入：連線預約 F 與節點占用 O_n（直接修改 P）                     */
/* ================================================================== */
static void put(Problem *P, int node, Curve *cv) {
    curve_add(&P->O[node], cv);
    curve_free(cv);
}

void commit(Problem *P, const Schedule *sch) {
    Rat S = P->S;

    /* 1. 每一跳的傳輸時段加進那條連線的 F */
    for (int i = 0; i < sch->n; i++) {
        Contact *c = &P->cs[sch->c[i]];
        iv_push(&c->F, sch->s[i], radd(sch->s[i], rdiv(S, c->r)));
    }

    /* 2a. 來源：g 起整包占著，s0 開始送、f0 送完 */
    const Contact *c0 = &P->cs[sch->c[0]];
    Rat s0 = sch->s[0], f0 = radd(s0, rdiv(S, c0->r));
    Curve cv;
    curve_init(&cv);
    if (rlt(P->g, s0)) {
        /* ts [g, s0, f0]，ls [0, S, 0]，rs [S, S, 0]：g 這點從 0 跳到 S */
        curve_push(&cv, P->g, R(0), S);
        curve_push(&cv, s0, S, S);
        curve_push(&cv, f0, R(0), R(0));
    } else {
        /* 一產生就送：ts [s0, f0]，ls [0, 0]，rs [S, 0] */
        curve_push(&cv, s0, R(0), S);
        curve_push(&cv, f0, R(0), R(0));
    }
    put(P, P->src, &cv);

    /* 2b. 中繼：三種形狀 */
    for (int i = 0; i + 1 < sch->n; i++) {
        const Contact *c1 = &P->cs[sch->c[i]], *c2 = &P->cs[sch->c[i + 1]];
        Rat h = radd(sch->s[i], c1->d);
        Rat A = radd(h, rdiv(S, c1->r));
        Rat s2 = sch->s[i + 1];
        Rat f = radd(s2, rdiv(S, c2->r));
        curve_init(&cv);
        if (P->ct && rlt(s2, A)) {
            /* 邊收邊轉、收和送重疊：在 sorted({h, A, s2, f}) 算「已收 − 已送」，ls = rs */
            Rat pts[4] = { h, A, s2, f }, u[4];
            int n = 0;
            for (int a = 0; a < 4; a++) {                 /* 去重並排序（最多 4 個） */
                int dup = 0;
                for (int b = 0; b < n; b++) if (req(u[b], pts[a])) dup = 1;
                if (!dup) u[n++] = pts[a];
            }
            for (int a = 1; a < n; a++)
                for (int b = a; b > 0 && rlt(u[b], u[b - 1]); b--) { Rat t = u[b]; u[b] = u[b - 1]; u[b - 1] = t; }
            for (int a = 0; a < n; a++) {
                Rat v = rsub(ramp(u[a], h, A, S), ramp(u[a], s2, f, S));
                curve_push(&cv, u[a], v, v);
            }
        } else if (rlt(A, s2)) {
            /* 收完後等一陣子才送：升、持平、降 */
            curve_push(&cv, h, R(0), R(0));
            curve_push(&cv, A, S, S);
            curve_push(&cv, s2, S, S);
            curve_push(&cv, f, R(0), R(0));
        } else {
            /* 收完馬上送（A = s2）：升到 S 立刻降 */
            curve_push(&cv, h, R(0), R(0));
            curve_push(&cv, A, S, S);
            curve_push(&cv, f, R(0), R(0));
        }
        put(P, c1->v, &cv);
    }

    /* 2c. 目的地：h～A 升到 S，在 A 交付歸零（A 的 ls = S、rs = 0） */
    const Contact *cl = &P->cs[sch->c[sch->n - 1]];
    Rat h = radd(sch->s[sch->n - 1], cl->d);
    Rat A = radd(h, rdiv(S, cl->r));
    curve_init(&cv);
    curve_push(&cv, h, R(0), R(0));
    curve_push(&cv, A, S, R(0));
    put(P, P->dst, &cv);
}
