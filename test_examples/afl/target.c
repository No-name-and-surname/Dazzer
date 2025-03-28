// target.c
#include <stdio.h>
#include <stdlib.h>
#include <json-c/json.h>

int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r");
    if (!f) return 1;

    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *buffer = malloc(fsize + 1);
    fread(buffer, fsize, 1, f);
    buffer[fsize] = 0;
    fclose(f);

    // Парсинг JSON
    json_object *jobj = json_tokener_parse(buffer);
    if (jobj)
        json_object_put(jobj);

    free(buffer);
    return 0;
}
