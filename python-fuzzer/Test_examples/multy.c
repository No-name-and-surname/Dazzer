#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

void* threadFunction(void* arg) {
    int threadID = *((int*)arg);
    int sleepTime = *((int*)(arg + sizeof(int))); // Получаем время задержки

    printf("Поток %d запущен. Задержка: %d секунд.\n", threadID, sleepTime);
    
    // Симуляция работы потока
    sleep(sleepTime);
    
    printf("Поток %d завершен.\n", threadID);
    free(arg); // освобождаем выделенную память
    return NULL;
}

int main() {
    int numThreads, sleepTime;
    printf("Введите количество потоков: ");
    scanf("%d", &numThreads);
    
    printf("Введите время задержки (в секундах): ");
    scanf("%d", &sleepTime);

    pthread_t* threads = malloc(numThreads * sizeof(pthread_t));

    for (int i = 0; i < numThreads; i++) {
        int* threadData = malloc(2 * sizeof(int));
        threadData[0] = 3;
        threadData[1] = 1;

        if (pthread_create(&threads[i], NULL, threadFunction, threadData) != 0) {
            perror("Ошибка при создании потока");
            free(threadData);
            free(threads);
            return 1;
        }
    }
    for (int i = 0; i < numThreads; i++) {
        pthread_join(threads[i], NULL);
    }

    free(threads);
    printf("Все потоки завершены.\n");
    return 0;
}
