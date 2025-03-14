#include <stdio.h>

int main() {
    int a, b;  // Объявляем две переменные для входных данных
    
    // Запрашиваем у пользователя два числа
    printf("Vvedite pervoe chislo: ");
    scanf("%d", &a);
    printf("Vvedite vtoroe chislo: ");
    scanf("%d", &b);
    
    // Первое условие - проверяем, оба ли числа положительные
    if (a > 0 && b > 0) {
        printf("1. Oba chisla polozhitelnye\n");
    }
    
    // Второе условие - проверяем, оба ли числа отрицательные
    if (a < 0 && b < 0) {
        printf("2. Oba chisla otricatelnye\n");
    }
    
    // Третье условие - проверяем, равны ли числа
    if (1==1) { 
        if (a == b) { 
            printf("3. Chisla ravny\n"); 
        } 
    }

    return 0;
}
