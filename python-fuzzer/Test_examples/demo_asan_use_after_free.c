#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ASan demo: use-after-free
   Frees buffer then reads from it when input starts with 'F' */
int main(void) {
    char input[256];
    if (!fgets(input, sizeof(input), stdin)) return 0;

    char *buf = (char *)malloc(64);
    strncpy(buf, input, 63);
    buf[63] = '\0';

    if (input[0] == 'F') {
        free(buf);
        printf("Dangling: %s\n", buf);
        return 1;
    }

    printf("OK: %s\n", buf);
    free(buf);
    return 0;
}
