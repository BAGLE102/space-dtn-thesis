/*
 * rat.h：精確有理數（分數），對應 Python 的 fractions.Fraction。
 *
 * 分子、分母各 64 位元，中間運算用 128 位元，結果一定約分、分母 > 0。
 * 約分後若超出 64 位元，印出錯誤並結束（不會默默算錯）。
 *
 * 為什麼不用 double：Buffer「剛好等於上限」這種邊界很多，
 * 浮點誤差會把可行判成不可行，或反過來。
 */
#ifndef RAT_H
#define RAT_H

#include <stdio.h>
#include <stdlib.h>

typedef struct {
    long long n;   /* 分子 */
    long long d;   /* 分母，永遠 > 0 */
} Rat;

typedef __int128 i128;

static i128 gcd128(i128 a, i128 b) {
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    while (b) { i128 t = a % b; a = b; b = t; }
    return a;
}

/* 約分並檢查範圍 */
static inline Rat rnorm(i128 n, i128 d) {
    if (d == 0) { fprintf(stderr, "rat: 除以 0\n"); exit(2); }
    if (d < 0) { n = -n; d = -d; }
    i128 g = gcd128(n, d);
    if (g > 1) { n /= g; d /= g; }
    if (n > (i128)9000000000000000000LL || n < -(i128)9000000000000000000LL ||
        d > (i128)9000000000000000000LL) {
        fprintf(stderr, "rat: 數值超出 64 位元範圍\n");
        exit(2);
    }
    Rat r = { (long long)n, (long long)d };
    return r;
}

static inline Rat R(long long n) { Rat r = { n, 1 }; return r; }         /* 整數 */
static inline Rat RQ(long long n, long long d) { return rnorm(n, d); }   /* n/d */

static inline Rat radd(Rat a, Rat b) { return rnorm((i128)a.n * b.d + (i128)b.n * a.d, (i128)a.d * b.d); }
static inline Rat rsub(Rat a, Rat b) { return rnorm((i128)a.n * b.d - (i128)b.n * a.d, (i128)a.d * b.d); }
static inline Rat rmul(Rat a, Rat b) { return rnorm((i128)a.n * b.n, (i128)a.d * b.d); }
static inline Rat rdiv(Rat a, Rat b) { return rnorm((i128)a.n * b.d, (i128)a.d * b.n); }

/* 比較：回傳 -1、0、1 */
static inline int rcmp(Rat a, Rat b) {
    i128 x = (i128)a.n * b.d, y = (i128)b.n * a.d;
    return (x > y) - (x < y);
}
static inline int rlt(Rat a, Rat b) { return rcmp(a, b) < 0; }
static inline int rle(Rat a, Rat b) { return rcmp(a, b) <= 0; }
static inline int rgt(Rat a, Rat b) { return rcmp(a, b) > 0; }
static inline int rge(Rat a, Rat b) { return rcmp(a, b) >= 0; }
static inline int req(Rat a, Rat b) { return a.n == b.n && a.d == b.d; }   /* 已約分，可直接比 */
static inline Rat rmax(Rat a, Rat b) { return rlt(a, b) ? b : a; }
static inline Rat rmin(Rat a, Rat b) { return rlt(b, a) ? b : a; }

/* 印成 p/q（整數只印 p） */
static inline void rprint(FILE *f, Rat a) {
    if (a.d == 1) fprintf(f, "%lld", a.n);
    else fprintf(f, "%lld/%lld", a.n, a.d);
}

/* 讀 "p" 或 "p/q" */
static inline Rat rparse(const char *s) {
    long long n, d = 1;
    if (sscanf(s, "%lld/%lld", &n, &d) < 1) { fprintf(stderr, "rat: 無法解析 %s\n", s); exit(2); }
    return rnorm(n, d);
}

#endif
