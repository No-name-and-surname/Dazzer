#include <stdio.h>
#include <string.h>

/* ASan demo: stack-buffer-overflow
   Copies long input into small stack buffer */
int main(void) {
    char input[256];
    if (!fgets(input, sizeof(input), stdin)) return 0;

    char local_buffer[32];

    if (strlen(input) > 32) {
        memcpy(local_buffer, input, strlen(input));
    }

    printf("buf: %s\n", local_buffer);
    return 0;
}
