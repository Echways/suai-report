// stats.cpp — статистика по числам из текстового файла
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

struct Stats {
    std::size_t count = 0;
    double sum = 0;
    double min = 0;
    double max = 0;
    double mean = 0;
    double deviation = 0;
};

// Читает числа из файла path в values. Возвращает false и текст
// ошибки, если файл не открылся или в нём встретилось не число.
bool readNumbers(const std::string& path, std::vector<double>& values,
                 std::string& error) {
    std::ifstream in(path);
    if (!in) {
        error = "не удалось открыть файл " + path;
        return false;
    }
    double x;
    while (in >> x) {
        values.push_back(x);
    }
    if (!in.eof()) {  // чтение остановилось не в конце файла
        in.clear();
        std::string token;
        in >> token;
        error = "не число: " + token;
        return false;
    }
    return true;
}

Stats compute(const std::vector<double>& values) {
    Stats s;
    s.count = values.size();
    if (s.count == 0) {
        return s;
    }
    s.min = s.max = values.front();
    for (double x : values) {
        s.sum += x;
        if (x < s.min) s.min = x;
        if (x > s.max) s.max = x;
    }
    s.mean = s.sum / s.count;
    double squares = 0;
    for (double x : values) {
        squares += (x - s.mean) * (x - s.mean);
    }
    s.deviation = std::sqrt(squares / s.count);
    return s;
}

void print(const Stats& s) {
    std::cout << std::fixed << std::setprecision(4)
              << "Количество: " << s.count << '\n'
              << "Сумма:      " << s.sum << '\n'
              << "Минимум:    " << s.min << '\n'
              << "Максимум:   " << s.max << '\n'
              << "Среднее:    " << s.mean << '\n'
              << "СКО:        " << s.deviation << '\n';
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Использование: stats ФАЙЛ\n";
        return 2;
    }
    std::vector<double> values;
    std::string error;
    if (!readNumbers(argv[1], values, error)) {
        std::cerr << "Ошибка: " << error << '\n';
        return 1;
    }
    if (values.empty()) {
        std::cerr << "Ошибка: в файле нет чисел\n";
        return 1;
    }
    print(compute(values));
    return 0;
}
