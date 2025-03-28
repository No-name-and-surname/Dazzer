#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Функция для обработки данных (логика из оригинального cov_test.c)
int process_numbers(int number1, int number2) {
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

    return 0; // Возвращаем 0, чтобы показать, что ошибок нет
}

// Функция входа для LibFuzzer
int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    // Нам нужно минимум 8 байт данных (два 4-байтовых целых числа)
    if (size < 8) return 0;
    
    // Преобразуем первые 4 байта в первое число
    int number1 = *(int*)data;
    
    // Преобразуем следующие 4 байта во второе число
    int number2 = *(int*)(data + 4);
    
    // Вызываем функцию обработки
    process_numbers(number1, number2);
    
    return 0;  // Всегда возвращаем 0
}
