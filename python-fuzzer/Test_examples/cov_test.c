#include <stdio.h>

int main() {
    int number1, number2;
    
    // Первое число
    printf("Введите первое число: ");
    scanf("%d", &number1);
    
    // Второе число
    printf("Введите второе число: ");
    scanf("%d", &number2);

    // Базовые проверки
    if (number1 == number2) {
        printf("Числа равны\n");
        if (number1 > 0) {
            printf("И оба положительные\n");
        }
    } else {
        printf("Числа не равны\n");
        if (number2 == 0) {
            printf("Второе число - ноль\n");
            if (number1 > 0) {
                printf("А первое положительное\n");
            }
        }
    }

    // Проверки на комбинации
    if (number1 + number2 == 2) {
        printf("Сумма равна 2\n");
        if (number1 == 1 && number2 == 1) {
            printf("Оба числа равны 1\n");
        }
    }

    // Специальные проверки для 1,0
    if (number1 == 1 && number2 == 0) {
        printf("Первое 1, второе 0\n");
        if (number1 > number2) {
            printf("Первое больше второго\n");
        }
    }

    // Проверяем сумму
    if (number1 + number2 > 1) {
        printf("Сумма больше 1\n");
    }

    // Обработка первого числа
    if (number1 > 0) {
        printf("Первое число положительное.\n");
    }
    if (number1 < 0) {
        printf("Первое число отрицательное.\n");
    }
    if (number1 == 0) {
        printf("Первое число равно нулю.\n");
    }
    if (number1 % 2 == 0) {
        printf("Первое число четное.\n");
    }
    if (number1 % 2 != 0) {
        printf("Первое число нечетное.\n");
    }

    // Обработка второго числа
    if (number2 > 0) {
        printf("Второе число положительное.\n");
    }
    if (number2 < 0) {
        printf("Второе число отрицательное.\n");
    }
    if (number2 == 0) {
        printf("Второе число равно нулю.\n");
    }
    if (number2 % 2 == 0) {
        printf("Второе число четное.\n");
    }
    if (number2 % 2 != 0) {
        printf("Второе число нечетное.\n");
    }

    return 0;
}
