#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int a;
    int b;
    char type[20];
    float value;
} Parameters;

int is_even(int num) {
    return num % 2 == 0;
}

int is_prime(int num) {
    if (num <= 1) return 0;
    if (num <= 3) return 1;
    if (num % 2 == 0 || num % 3 == 0) return 0;
    
    for (int i = 5; i * i <= num; i += 6) {
        if (num % i == 0 || num % (i + 2) == 0) return 0;
    }
    return 1;
}

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int fibonacci(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

void process_string_parameter(const char* str) {
    if (str == NULL) {
        printf("Null string parameter\n");
        return;
    }
    
    if (strlen(str) == 0) {
        printf("Empty string parameter\n");
        return;
    }
    
    if (strcmp(str, "debug") == 0) {
        printf("Debug mode activated\n");
    } else if (strcmp(str, "verbose") == 0) {
        printf("Verbose mode activated\n");
    } else if (strcmp(str, "silent") == 0) {
        printf("Silent mode activated\n");
    } else if (strncmp(str, "level", 5) == 0) {
        int level = atoi(str + 5);
        if (level >= 1 && level <= 5) {
            printf("Level %d selected\n", level);
        } else {
            printf("Invalid level value\n");
        }
    } else {
        printf("Unknown parameter: %s\n", str);
    }
}

float math_operation(int a, int b, const char* op) {
    if (strcmp(op, "add") == 0) {
        return a + b;
    } else if (strcmp(op, "subtract") == 0) {
        return a - b;
    } else if (strcmp(op, "multiply") == 0) {
        return a * b;
    } else if (strcmp(op, "divide") == 0) {
        if (b == 0) {
            printf("Error: Division by zero\n");
            return 0;
        }
        return (float)a / b;
    } else if (strcmp(op, "power") == 0) {
        float result = 1;
        for (int i = 0; i < b; i++) {
            result *= a;
        }
        return result;
    } else if (strcmp(op, "max") == 0) {
        return a > b ? a : b;
    } else if (strcmp(op, "min") == 0) {
        return a < b ? a : b;
    } else {
        printf("Unknown operation: %s\n", op);
        return 0;
    }
}

void process_parameters(Parameters* params) {
    if (params == NULL) {
        printf("Null parameters\n");
        return;
    }
    
    if (params->a < 0) {
        printf("Parameter A is negative: %d\n", params->a);
    } else if (params->a == 0) {
        printf("Parameter A is zero\n");
    } else {
        printf("Parameter A is positive: %d\n", params->a);
        
        if (is_even(params->a)) {
            printf("Parameter A is even\n");
        } else {
            printf("Parameter A is odd\n");
        }
        
        if (is_prime(params->a)) {
            printf("Parameter A is prime\n");
        }
        
        if (params->a < 10) {
            printf("Factorial of A: %d\n", factorial(params->a));
        }
        
        if (params->a < 20) {
            printf("Fibonacci value for A: %d\n", fibonacci(params->a));
        }
    }
    
    if (params->b < 0) {
        printf("Parameter B is negative: %d\n", params->b);
    } else if (params->b == 0) {
        printf("Parameter B is zero\n");
    } else {
        printf("Parameter B is positive: %d\n", params->b);
        
        if (is_even(params->b)) {
            printf("Parameter B is even\n");
        } else {
            printf("Parameter B is odd\n");
        }
        
        if (is_prime(params->b)) {
            printf("Parameter B is prime\n");
        }
    }
    
    if (params->a == params->b) {
        printf("A equals B\n");
    } else if (params->a > params->b) {
        printf("A is greater than B\n");
    } else {
        printf("A is less than B\n");
    }
    
    int sum = params->a + params->b;
    if (sum < 0) {
        printf("Sum is negative: %d\n", sum);
    } else if (sum == 0) {
        printf("Sum is zero\n");
    } else {
        printf("Sum is positive: %d\n", sum);
        if (is_even(sum)) {
            printf("Sum is even\n");
        } else {
            printf("Sum is odd\n");
        }
    }
    
    process_string_parameter(params->type);
    
    float result = math_operation(params->a, params->b, params->type);
    params->value = result;
    printf("Operation result: %f\n", result);
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        printf("Usage: %s <a> <b> <type>\n", argv[0]);
        return 1;
    }
    
    Parameters params;
    params.a = atoi(argv[1]);
    params.b = atoi(argv[2]);
    strncpy(params.type, argv[3], 19);
    params.type[19] = '\0';
    params.value = 0.0;
    
    process_parameters(&params);
    
    return 0;
}
