#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BUFFER 128
#define MAX_OBJECTS 10

typedef struct {
    char name[64];
    int value;
    void* data;
    int data_size;
} Object;

Object* objects[MAX_OBJECTS];
int object_count = 0;

void cleanup() {
    for (int i = 0; i < object_count; i++) {
        if (objects[i] != NULL && objects[i]->data != NULL) {
            free(objects[i]->data);
        }
        if (objects[i] != NULL) {
            free(objects[i]);
        }
    }
    object_count = 0;
}

int add_object(const char* name, int value, const void* data, int data_size) {
    if (object_count >= MAX_OBJECTS) {
        return -1;
    }
    
    Object* obj = (Object*)malloc(sizeof(Object));
    if (obj == NULL) {
        return -2;
    }
    
    strncpy(obj->name, name, 63);
    obj->name[63] = '\0';
    obj->value = value;
    
    if (data != NULL && data_size > 0) {
        obj->data = malloc(data_size);
        if (obj->data == NULL) {
            free(obj);
            return -3;
        }
        memcpy(obj->data, data, data_size);
        obj->data_size = data_size;
    } else {
        obj->data = NULL;
        obj->data_size = 0;
    }
    
    objects[object_count] = obj;
    object_count++;
    return object_count - 1;
}

Object* find_object(const char* name) {
    for (int i = 0; i < object_count; i++) {
        if (strcmp(objects[i]->name, name) == 0) {
            return objects[i];
        }
    }
    return NULL;
}

int process_input(const char* input) {
    char buffer[MAX_BUFFER];
    char command[32];
    char name[64];
    int value;
    
    strcpy(buffer, input);
    
    int params = sscanf(buffer, "%s %s %d", command, name, &value);
    if (params < 1) {
        printf("Invalid command format\n");
        return -1;
    }
    
    if (strcmp(command, "add") == 0) {
        if (params < 3) {
            printf("Add command requires name and value\n");
            return -1;
        }
        
        char* data_str = strstr(buffer, name) + strlen(name);
        data_str = strstr(data_str, " ") + 1;
        data_str = strstr(data_str, " ") + 1;
        
        int id = add_object(name, value, data_str, strlen(data_str));
        if (id >= 0) {
            printf("Added object with ID: %d\n", id);
            return id;
        } else {
            printf("Failed to add object: %d\n", id);
            return -1;
        }
    } else if (strcmp(command, "find") == 0) {
        if (params < 2) {
            printf("Find command requires name\n");
            return -1;
        }
        
        Object* obj = find_object(name);
        if (obj != NULL) {
            printf("Found object: %s, value: %d\n", obj->name, obj->value);
            return 0;
        } else {
            printf("Object not found: %s\n", name);
            return -1;
        }
    } else if (strcmp(command, "delete") == 0) {
        if (params < 2) {
            printf("Delete command requires name\n");
            return -1;
        }
        
        for (int i = 0; i < object_count; i++) {
            if (strcmp(objects[i]->name, name) == 0) {
                if (objects[i]->data != NULL) {
                    free(objects[i]->data);
                }
                free(objects[i]);
                
                for (int j = i; j < object_count - 1; j++) {
                    objects[j] = objects[j + 1];
                }
                object_count--;
                printf("Deleted object: %s\n", name);
                return 0;
            }
        }
        
        printf("Object not found for deletion: %s\n", name);
        return -1;
    } else if (strcmp(command, "update") == 0) {
        if (params < 3) {
            printf("Update command requires name and value\n");
            return -1;
        }
        
        Object* obj = find_object(name);
        if (obj != NULL) {
            obj->value = value;
            
            char* data_str = strstr(buffer, name) + strlen(name);
            data_str = strstr(data_str, " ") + 1;
            data_str = strstr(data_str, " ") + 1;
            
            if (data_str != NULL && strlen(data_str) > 0) {
                if (obj->data != NULL) {
                    free(obj->data);
                }
                
                obj->data = malloc(strlen(data_str));
                memcpy(obj->data, data_str, strlen(data_str));
                obj->data_size = strlen(data_str);
            }
            
            printf("Updated object: %s\n", name);
            return 0;
        } else {
            printf("Object not found for update: %s\n", name);
            return -1;
        }
    } else {
        printf("Unknown command: %s\n", command);
        return -1;
    }
}

int parse_data(const char* data) {
    if (data == NULL) {
        return -1;
    }
    
    int length = strlen(data);
    if (length == 0) {
        return 0;
    }
    
    if (data[0] == '{') {
        if (data[length - 1] != '}') {
            printf("Invalid JSON: missing closing brace\n");
            return -1;
        }
        
        const char* content = data + 1;
        int content_length = length - 2;
        
        char* working_copy = (char*)malloc(content_length + 1);
        if (working_copy == NULL) {
            return -1;
        }
        
        strncpy(working_copy, content, content_length);
        working_copy[content_length] = '\0';
        
        char* token = strtok(working_copy, ",");
        while (token != NULL) {
            char key[64] = {0};
            char value[128] = {0};
            
            if (sscanf(token, "\"%[^\"]\":\"%[^\"]\"", key, value) == 2 ||
                sscanf(token, "\"%[^\"]\":%[^,}]", key, value) == 2) {
                printf("Key: %s, Value: %s\n", key, value);
            } else {
                printf("Invalid key-value pair: %s\n", token);
            }
            
            token = strtok(NULL, ",");
        }
        
        free(working_copy);
        return 1;
    } else {
        return 0;
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <command string>\n", argv[0]);
        return 1;
    }
    
    atexit(cleanup);
    
    char* input = argv[1];
    int result = process_input(input);
    
    if (result >= 0 && object_count > 0) {
        Object* last = objects[object_count - 1];
        if (last->data != NULL) {
            parse_data((const char*)last->data);
        }
    }
    
    return 0;
}
