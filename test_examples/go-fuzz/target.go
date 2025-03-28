// target.go
package json

import "encoding/json"

// Функция-мишень для Go-fuzz
func Fuzz(data []byte) int {
    var j interface{}
    if err := json.Unmarshal(data, &j); err != nil {
        return 0
    }
    return 1
}
