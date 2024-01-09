#include <iostream>
#include <string>
#include <vector>
#include <chrono>

struct Row {
    std::string id;
    std::string name;
    std::string key_for_search;
};

void main(void) {
    std::vector<Row> rows;
    for (int i = 1; i <= 250000; i++) {
        const auto s = std::to_string(i);
        rows.push_back({
            s,
            "Row " + s,
            "row " + s
        });
    }

    const int block_size = 11;
    const int block_start = 0;
    const std::string query = "";

    auto t = std::chrono::steady_clock::now();
    std::vector<Row*> block_rows;
    int total = 0;
    for (auto& row : rows) {
        if (query.empty() || row.key_for_search.find(query) != std::string::npos) {
            if (total >= block_start && block_rows.size() < block_size) {
                block_rows.push_back(&row);
            }
            total++;
        }
    }
    auto dt = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t).count();
    std::cout << "dt: " << dt << " ms" << std::endl;
}
