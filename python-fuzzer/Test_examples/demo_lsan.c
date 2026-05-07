#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* LSan demo: memory leak
   Allocates memory but never frees it when input starts with 'L' */
int main(void) {
    char input[256];
    if (!fgets(input, sizeof(input), stdin)) return 0;

    int count = atoi(input);
    if (count <= 0) count = 1;
    if (count > 100) count = 100;

    for (int i = 0; i < count; i++) {
        char *leaked = (char *)malloc(1024);
        if (!leaked) break;
        memset(leaked, 'A', 1024);
        printf("allocated block %d\n", i);
        /* intentionally no free(leaked) */
    }

    return 0;
}
