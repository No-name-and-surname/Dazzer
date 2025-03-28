// target.cpp
#include <cstddef>
#include <cstdint>
#include <json/json.h>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    // Конвертируем в строку и добавляем нулевой символ
    std::string input(reinterpret_cast<const char*>(data), size);

    Json::Value root;
    Json::Reader reader;
    
    // Попытка парсинга JSON
    reader.parse(input, root);
    
    return 0;  // Значение не имеет значения для LibFuzzer
}
