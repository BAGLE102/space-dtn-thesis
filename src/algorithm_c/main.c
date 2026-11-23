/*
 * main.c：執行方式
 *
 *   ./dtn example          跑教材第 4、9 章的例子（收完才轉、邊收邊轉各一次）
 *   ./dtn 輸入檔           依序規劃輸入檔裡的每一包，每包排定後 commit
 *
 * 輸入檔格式（每行一筆，# 開頭為註解；數字可寫成 p 或 p/q）：
 *   nodes N                         節點數，編號 0 .. N-1（必須第一行）
 *   contact id u v a b r d          一條連線
 *   background n t1 l1 r1 t2 l2 r2 ...   節點 n 的初始占用曲線（可省略）
 *   param S M T ct                  包大小、Buffer 上限、期限、1 = 邊收邊轉
 *   bundle u v g                    一包：來源、目的地、產生時間（依序規劃）
 *
 * 輸出每包一行：
 *   bundle i: none
 *   bundle i: arr 到達時間 連線@出發時間 連線@出發時間 ...
 */
#include <string.h>
#include "dtn.h"

static void print_result(FILE *f, int i, const Problem *P, const Schedule *sch, int ok) {
    fprintf(f, "bundle %d: ", i);
    if (!ok) { fprintf(f, "none\n"); return; }
    fprintf(f, "arr ");
    rprint(f, arrival(P, sch));
    for (int k = 0; k < sch->n; k++) {
        fprintf(f, " %s@", P->cs[sch->c[k]].id);
        rprint(f, sch->s[k]);
    }
    fprintf(f, "\n");
}

static void free_problem(Problem *P) {
    for (int c = 0; c < P->nc; c++) iv_free(&P->cs[c].F);
    for (int n = 0; n < P->nn; n++) curve_free(&P->O[n]);
    free(P->cs); free(P->O);
}

/* ---------- 教材例子 ---------- */
static Contact make_contact(const char *id, int u, int v, long long a, long long b) {
    Contact c;
    memset(&c, 0, sizeof c);
    strncpy(c.id, id, sizeof c.id - 1);
    c.u = u; c.v = v; c.a = R(a); c.b = R(b); c.r = R(1); c.d = R(0);
    iv_init(&c.F);
    return c;
}

static int run_example(void) {
    for (int ct = 0; ct <= 1; ct++) {
        Problem P;
        memset(&P, 0, sizeof P);
        /* 節點 0 = A、1 = B、2 = C */
        P.nc = 2;
        P.cs = malloc(sizeof(Contact) * 2);
        P.cs[0] = make_contact("c1", 0, 1, 100, 150);   /* A→B 開 100～150 */
        P.cs[1] = make_contact("c2", 1, 2, 110, 160);   /* B→C 開 110～160 */
        P.nn = 3;
        P.O = malloc(sizeof(Curve) * 3);
        for (int n = 0; n < 3; n++) curve_init(&P.O[n]);
        /* B 上的舊包：ts [100, 110, 120, 130]，值 [0, 10, 10, 0] */
        long long ts[4] = { 100, 110, 120, 130 }, vs[4] = { 0, 10, 10, 0 };
        for (int k = 0; k < 4; k++) curve_push(&P.O[1], R(ts[k]), R(vs[k]), R(vs[k]));
        P.src = 0; P.dst = 2; P.g = R(100); P.S = R(10); P.M = R(15); P.T = R(1000); P.ct = ct;

        Schedule sch = { 0, NULL, NULL };
        int ok = plan(&P, &sch);
        printf("%s\n", ct ? "邊收邊轉" : "收完才轉");
        if (!ok) { printf("  找不到\n"); free_problem(&P); continue; }
        for (int k = 0; k < sch.n; k++) {
            printf("  %s 在 ", P.cs[sch.c[k]].id);
            rprint(stdout, sch.s[k]);
            printf(" 出發\n");
        }
        printf("  ");
        rprint(stdout, arrival(&P, &sch));
        printf(" 到 C，回放檢查：%s\n", validate(&P, &sch) ? "通過" : "失敗");
        commit(&P, &sch);
        printf("  排定後 B 的 O_n：ts =");
        for (int k = 0; k < P.O[1].n; k++) { printf(" "); rprint(stdout, P.O[1].ts[k]); }
        printf("\n                   值 =");
        for (int k = 0; k < P.O[1].n; k++) { printf(" "); rprint(stdout, P.O[1].ls[k]); }
        printf("\n");
        sched_free(&sch);
        free_problem(&P);
    }
    return 0;
}

/* ---------- 讀輸入檔 ---------- */
static int run_file(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return 1; }
    Problem P;
    memset(&P, 0, sizeof P);
    int capc = 0, bundle = 0;
    char line[1 << 16];
    while (fgets(line, sizeof line, f)) {
        char *tok = strtok(line, " \t\r\n");
        if (!tok || tok[0] == '#') continue;
        if (!strcmp(tok, "nodes")) {
            P.nn = atoi(strtok(NULL, " \t\r\n"));
            P.O = malloc(sizeof(Curve) * P.nn);
            for (int n = 0; n < P.nn; n++) curve_init(&P.O[n]);
        } else if (!strcmp(tok, "contact")) {
            if (P.nc == capc) { capc = capc ? capc * 2 : 16; P.cs = realloc(P.cs, sizeof(Contact) * capc); }
            Contact *c = &P.cs[P.nc++];
            memset(c, 0, sizeof *c);
            strncpy(c->id, strtok(NULL, " \t\r\n"), sizeof c->id - 1);
            c->u = atoi(strtok(NULL, " \t\r\n"));
            c->v = atoi(strtok(NULL, " \t\r\n"));
            c->a = rparse(strtok(NULL, " \t\r\n"));
            c->b = rparse(strtok(NULL, " \t\r\n"));
            c->r = rparse(strtok(NULL, " \t\r\n"));
            c->d = rparse(strtok(NULL, " \t\r\n"));
            iv_init(&c->F);
        } else if (!strcmp(tok, "background")) {
            int n = atoi(strtok(NULL, " \t\r\n"));
            char *t;
            while ((t = strtok(NULL, " \t\r\n"))) {
                Rat tt = rparse(t);
                Rat l = rparse(strtok(NULL, " \t\r\n"));
                Rat r = rparse(strtok(NULL, " \t\r\n"));
                curve_push(&P.O[n], tt, l, r);
            }
        } else if (!strcmp(tok, "param")) {
            P.S = rparse(strtok(NULL, " \t\r\n"));
            P.M = rparse(strtok(NULL, " \t\r\n"));
            P.T = rparse(strtok(NULL, " \t\r\n"));
            P.ct = atoi(strtok(NULL, " \t\r\n"));
        } else if (!strcmp(tok, "bundle")) {
            P.src = atoi(strtok(NULL, " \t\r\n"));
            P.dst = atoi(strtok(NULL, " \t\r\n"));
            P.g = rparse(strtok(NULL, " \t\r\n"));
            Schedule sch = { 0, NULL, NULL };
            int ok = plan(&P, &sch);
            if (ok && !validate(&P, &sch)) { printf("bundle %d: VALIDATION_FAILED\n", bundle++); sched_free(&sch); continue; }
            print_result(stdout, bundle++, &P, &sch, ok);
            if (ok) commit(&P, &sch);
            sched_free(&sch);
        }
    }
    fclose(f);
    free_problem(&P);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "用法：%s example | %s 輸入檔\n", argv[0], argv[0]);
        return 1;
    }
    if (!strcmp(argv[1], "example")) return run_example();
    return run_file(argv[1]);
}
