#include <stdio.h>
#include <string.h>

int main(void) {
    char input[256];
    char buf[16];

    if (!fgets(input, sizeof(input), stdin)) return 0;

    if (strstr(input, "OVERFLOW") != NULL) {
        strcpy(buf, input);
        puts(buf);
        return 1;
    }

    puts("ok");
    return 0;
}
