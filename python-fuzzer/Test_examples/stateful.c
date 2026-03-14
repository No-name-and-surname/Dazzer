#include <stdio.h>
#include <string.h>

int main(void) {
    char a[128], b[128];
    if (!fgets(a, sizeof(a), stdin)) return 0;
    if (!fgets(b, sizeof(b), stdin)) return 0;

    if (strstr(a, "MAGIC") && strstr(b, "TRIGGER")) {
        fprintf(stderr, "panic: interesting path reached\n");
        return 2;
    }

    if (strstr(a, "A") && strstr(b, "B")) {
        puts("branch-1");
    } else {
        puts("branch-2");
    }

    return 0;
}
