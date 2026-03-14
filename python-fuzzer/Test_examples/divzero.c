#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char a_buf[64], b_buf[64];
    if (!fgets(a_buf, sizeof(a_buf), stdin)) return 0;
    if (!fgets(b_buf, sizeof(b_buf), stdin)) return 0;

    int a = atoi(a_buf);
    int b = atoi(b_buf);

    if (b == 0) {
        volatile int crash = a / b;
        (void)crash;
    }

    printf("%d\n", a / (b == 0 ? 1 : b));
    return 0;
}
