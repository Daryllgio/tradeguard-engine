#pragma once

#include <string>

struct BenchmarkMetrics {
    long long runtimeMicros{};
    int candlesProcessed{};
    int decisionsLogged{};
    int tradesExecuted{};
    double microsPerCandle{};
    double candlesPerSecond{};
};

class Benchmark {
public:
    static void writeReport(const std::string& path, const BenchmarkMetrics& metrics);
};
