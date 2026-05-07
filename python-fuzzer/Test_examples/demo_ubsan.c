#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

/* UBSan demo: signed integer overflow + shift exponent
   Triggers on large numbers or negative shift */
int main(void) {
    char buf[64];
    if (!fgets(buf, sizeof(buf), stdin)) return 0;

    int a = atoi(buf);

    if (a > 100000) {
        int result = a * a * a;
        printf("cube: %d\n", result);
    } else if (a < 0) {
        int shifted = 1 << (-a);
        printf("shifted: %d\n", shifted);
    } else {
        printf("ok: %d\n", a * 2);
    }

    return 0;
}
