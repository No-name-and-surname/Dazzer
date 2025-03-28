#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

#define MAX_ITEMS 1000
#define NUM_THREADS 4
#define CHUNK_SIZE (MAX_ITEMS / NUM_THREADS)

typedef struct {
    int id;
    char name[64];
    double value;
} Item;

typedef struct {
    int thread_id;
    Item* items;
    int start_index;
    int end_index;
    double* result;
} ThreadData;

Item items[MAX_ITEMS];
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
int processed_items = 0;
double global_sum = 0.0;

void initialize_items(const char* input_data) {
    char* data_copy = strdup(input_data);
    char* line = strtok(data_copy, ";");
    int index = 0;
    
    while (line != NULL && index < MAX_ITEMS) {
        int id;
        char name[64];
        double value;
        
        if (sscanf(line, "%d,%[^,],%lf", &id, name, &value) == 3) {
            items[index].id = id;
            strncpy(items[index].name, name, 63);
            items[index].name[63] = '\0';
            items[index].value = value;
            index++;
        }
        
        line = strtok(NULL, ";");
    }
    
    for (int i = index; i < MAX_ITEMS; i++) {
        items[i].id = i;
        sprintf(items[i].name, "Item %d", i);
        items[i].value = (double)rand() / RAND_MAX * 100.0;
    }
    
    free(data_copy);
}

double process_item(Item* item) {
    if (item->value < 0) {
        return 0.0;
    }
    
    if (strstr(item->name, "special") != NULL) {
        return item->value * 2.0;
    }
    
    if (item->id % 3 == 0) {
        return item->value * 1.5;
    }
    
    return item->value;
}

void* process_chunk(void* arg) {
    ThreadData* data = (ThreadData*)arg;
    double local_sum = 0.0;
    
    for (int i = data->start_index; i < data->end_index && i < MAX_ITEMS; i++) {
        double processed_value = process_item(&data->items[i]);
        local_sum += processed_value;
        
        pthread_mutex_lock(&mutex);
        processed_items++;
        global_sum += processed_value;
        pthread_mutex_unlock(&mutex);
        
        usleep(10);
    }
    
    *data->result = local_sum;
    return NULL;
}

double parallel_process_items() {
    pthread_t threads[NUM_THREADS];
    ThreadData thread_data[NUM_THREADS];
    double thread_results[NUM_THREADS] = {0.0};
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].items = items;
        thread_data[i].start_index = i * CHUNK_SIZE;
        thread_data[i].end_index = (i + 1) * CHUNK_SIZE;
        thread_data[i].result = &thread_results[i];
        
        if (pthread_create(&threads[i], NULL, process_chunk, &thread_data[i]) != 0) {
            fprintf(stderr, "Error creating thread %d\n", i);
            exit(1);
        }
    }
    
    double total_sum = 0.0;
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
        total_sum += thread_results[i];
    }
    
    return total_sum;
}

typedef struct {
    int thread_id;
    Item* items;
    int* indices;
    int num_indices;
    pthread_mutex_t* mutex;
} SearchThreadData;

void* search_thread(void* arg) {
    SearchThreadData* data = (SearchThreadData*)arg;
    
    for (int i = 0; i < data->num_indices; i++) {
        int index = data->indices[i];
        if (index >= 0 && index < MAX_ITEMS) {
            Item* item = &data->items[index];
            
            pthread_mutex_lock(data->mutex);
            printf("Thread %d found item %d: %s, value: %.2f\n", 
                   data->thread_id, item->id, item->name, item->value);
            pthread_mutex_unlock(data->mutex);
        }
        
        usleep(5000);
    }
    
    return NULL;
}

void parallel_search(int* indices, int num_indices) {
    if (num_indices <= 0) return;
    
    pthread_t threads[NUM_THREADS];
    SearchThreadData thread_data[NUM_THREADS];
    
    int indices_per_thread = (num_indices + NUM_THREADS - 1) / NUM_THREADS;
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].items = items;
        thread_data[i].indices = indices + (i * indices_per_thread);
        thread_data[i].num_indices = 
            (i == NUM_THREADS - 1) ? 
            (num_indices - i * indices_per_thread) : 
            indices_per_thread;
        thread_data[i].mutex = &mutex;
        
        if (thread_data[i].num_indices <= 0) continue;
        
        if (pthread_create(&threads[i], NULL, search_thread, &thread_data[i]) != 0) {
            fprintf(stderr, "Error creating search thread %d\n", i);
            exit(1);
        }
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        if (i * indices_per_thread < num_indices) {
            pthread_join(threads[i], NULL);
        }
    }
}

void update_item_values(double factor) {
    pthread_mutex_lock(&mutex);
    
    for (int i = 0; i < MAX_ITEMS; i++) {
        items[i].value *= factor;
    }
    
    pthread_mutex_unlock(&mutex);
}

typedef struct {
    double sum;
    int count;
} UpdateResult;

void* update_thread(void* arg) {
    int thread_id = *(int*)arg;
    int start = thread_id * CHUNK_SIZE;
    int end = (thread_id + 1) * CHUNK_SIZE;
    
    UpdateResult* result = (UpdateResult*)malloc(sizeof(UpdateResult));
    result->sum = 0.0;
    result->count = 0;
    
    for (int i = start; i < end && i < MAX_ITEMS; i++) {
        pthread_mutex_lock(&mutex);
        items[i].value += (double)thread_id;
        result->sum += items[i].value;
        pthread_mutex_unlock(&mutex);
        
        result->count++;
        usleep(5);
    }
    
    return result;
}

double parallel_update() {
    pthread_t threads[NUM_THREADS];
    int thread_ids[NUM_THREADS];
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_ids[i] = i;
        if (pthread_create(&threads[i], NULL, update_thread, &thread_ids[i]) != 0) {
            fprintf(stderr, "Error creating update thread %d\n", i);
            exit(1);
        }
    }
    
    double total = 0.0;
    int total_count = 0;
    
    for (int i = 0; i < NUM_THREADS; i++) {
        UpdateResult* result;
        pthread_join(threads[i], (void**)&result);
        
        total += result->sum;
        total_count += result->count;
        
        free(result);
    }
    
    return total_count > 0 ? total / total_count : 0.0;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <input_data>\n", argv[0]);
        return 1;
    }
    
    srand(time(NULL));
    initialize_items(argv[1]);
    
    printf("Processing items in parallel...\n");
    double sum = parallel_process_items();
    printf("Total sum: %.2f\n", sum);
    printf("Global sum: %.2f\n", global_sum);
    
    if (argc >= 3) {
        int num_search_indices = atoi(argv[2]);
        if (num_search_indices > 0) {
            int* search_indices = (int*)malloc(num_search_indices * sizeof(int));
            
            for (int i = 0; i < num_search_indices; i++) {
                search_indices[i] = rand() % MAX_ITEMS;
            }
            
            printf("Searching for items in parallel...\n");
            parallel_search(search_indices, num_search_indices);
            
            free(search_indices);
        }
    }
    
    printf("Updating item values in parallel...\n");
    double avg_value = parallel_update();
    printf("Average value after update: %.2f\n", avg_value);
    
    return 0;
}
