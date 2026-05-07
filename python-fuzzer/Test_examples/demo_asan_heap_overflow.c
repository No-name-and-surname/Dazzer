#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ASan demo: heap-buffer-overflow
   Writes beyond allocated heap buffer when input > 8 chars */
int main(void) {
    char input[256];
    if (!fgets(input, sizeof(input), stdin)) return 0;

    int len = (int)strlen(input);
    char *buf = (char *)malloc(8);

    if (len > 8) {
        memcpy(buf, input, len);
    } else {
        memcpy(buf, input, len);
    }

    printf("Got: %s\n", buf);
    free(buf);
    return 0;
}
