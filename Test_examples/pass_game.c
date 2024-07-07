#include <stdio.h>
#include <string.h>

int main() {
    char name[50];
    char password[50];

    printf("Enter your name: ");
    scanf("%s", name);

    if (strcmp(name, "name") == 0) {
        printf("Enter your password: ");
        scanf("%s", password);
        if (strcmp(password, "password") == 0) {
            printf("Ok\n");
        } else {
            printf("no\n");
        }
    } else {
        printf("no\n");
    }

    return 0;
}
