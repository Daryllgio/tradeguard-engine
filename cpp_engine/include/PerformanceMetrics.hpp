#pragma once

#include "Types.hpp"
#include <vector>

struct PerformanceMetrics {
    int totalDecisions{};
    int acceptedTrades{};
    int rejectedSetups{};
    int executedTrades{};
    double totalPnl{};
    double endingEquity{};
    double winRate{};
    double averagePnl{};
    double bestTrade{};
    double worstTrade{};
    double maxDrawdown{};
};

class PerformanceAnalyzer {
public:
    static PerformanceMetrics analyze(
        const std::vector<TradeDecision>& decisions,
        const std::vector<TradeResult>& trades,
        const std::vector<double>& equityCurve
    );
};
