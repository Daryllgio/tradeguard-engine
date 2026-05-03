#include "MarketData.hpp"
#include "CandleBuilder.hpp"
#include "Backtester.hpp"
#include "DecisionLogger.hpp"
#include "PerformanceMetrics.hpp"
#include "ConfigLoader.hpp"
#include "Benchmark.hpp"

#include <filesystem>
#include <iostream>
#include <chrono>

int main(int argc, char* argv[]) {
    try {
        std::string inputPath = argc > 1 ? argv[1] : "../data/sample_ticks.csv";
        std::string outputDir = argc > 2 ? argv[2] : "../output";
        std::string configPath = argc > 3 ? argv[3] : "../config/risk_config.json";

        std::filesystem::create_directories(outputDir);

        auto start = std::chrono::high_resolution_clock::now();

        auto ticks = MarketData::loadTicksFromCsv(inputPath);

        CandleBuilder builder(10);
        auto candles = builder.build(ticks);

        RiskConfig config = ConfigLoader::loadRiskConfig(configPath);

        Backtester backtester(config);
        backtester.run(candles);

        DecisionLogger::writeDecisions(outputDir + "/decisions.csv", backtester.decisions());
        DecisionLogger::writeTrades(outputDir + "/trades.csv", backtester.trades());
        DecisionLogger::writeEquityCurve(outputDir + "/equity_curve.csv", backtester.equityCurve());

        auto end = std::chrono::high_resolution_clock::now();
        auto micros = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();

        PerformanceMetrics metrics = PerformanceAnalyzer::analyze(
            backtester.decisions(),
            backtester.trades(),
            backtester.equityCurve()
        );

        BenchmarkMetrics benchmark;
        benchmark.runtimeMicros = micros;
        benchmark.candlesProcessed = static_cast<int>(candles.size());
        benchmark.decisionsLogged = static_cast<int>(backtester.decisions().size());
        benchmark.tradesExecuted = static_cast<int>(backtester.trades().size());
        benchmark.microsPerCandle = candles.empty() ? 0.0 : static_cast<double>(micros) / static_cast<double>(candles.size());
        benchmark.candlesPerSecond = micros == 0 ? 0.0 : static_cast<double>(candles.size()) / (static_cast<double>(micros) / 1'000'000.0);

        Benchmark::writeReport(outputDir + "/benchmark_report.txt", benchmark);

        std::cout << "TradeGuard Engine completed successfully.\n";
        std::cout << "Config loaded: " << configPath << "\n";
        std::cout << "Account equity: $" << config.accountEquity << "\n";
        std::cout << "Ticks loaded: " << ticks.size() << "\n";
        std::cout << "Candles built: " << candles.size() << "\n";
        std::cout << "Decisions logged: " << metrics.totalDecisions << "\n";
        std::cout << "Accepted trades: " << metrics.acceptedTrades << "\n";
        std::cout << "Rejected setups: " << metrics.rejectedSetups << "\n";
        std::cout << "Trades executed: " << metrics.executedTrades << "\n";
        std::cout << "Ending equity: $" << metrics.endingEquity << "\n";
        std::cout << "Total PnL: $" << metrics.totalPnl << "\n";
        std::cout << "Win rate: " << metrics.winRate << "%\n";
        std::cout << "Max drawdown: " << metrics.maxDrawdown << "%\n";
        std::cout << "Runtime: " << micros << " microseconds\n";
        std::cout << "Average latency: " << benchmark.microsPerCandle << " microseconds/candle\n";
        std::cout << "Throughput: " << benchmark.candlesPerSecond << " candles/second\n";
        std::cout << "Output written to: " << outputDir << "\n";

        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "TradeGuard Engine failed: " << ex.what() << "\n";
        return 1;
    }
}
