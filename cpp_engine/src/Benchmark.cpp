#include "Benchmark.hpp"
#include <fstream>
#include <stdexcept>

void Benchmark::writeReport(const std::string& path, const BenchmarkMetrics& metrics) {
    std::ofstream file(path);

    if (!file.is_open()) {
        throw std::runtime_error("Could not write benchmark report: " + path);
    }

    file << "# TradeGuard Engine Benchmark Report\n\n";
    file << "Runtime microseconds: " << metrics.runtimeMicros << "\n";
    file << "Candles processed: " << metrics.candlesProcessed << "\n";
    file << "Decisions logged: " << metrics.decisionsLogged << "\n";
    file << "Trades executed: " << metrics.tradesExecuted << "\n";
    file << "Average microseconds per candle: " << metrics.microsPerCandle << "\n";
    file << "Throughput candles per second: " << metrics.candlesPerSecond << "\n";
}
