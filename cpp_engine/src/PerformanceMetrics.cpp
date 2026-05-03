#include "PerformanceMetrics.hpp"
#include <algorithm>
#include <numeric>

PerformanceMetrics PerformanceAnalyzer::analyze(
    const std::vector<TradeDecision>& decisions,
    const std::vector<TradeResult>& trades,
    const std::vector<double>& equityCurve
) {
    PerformanceMetrics metrics;

    metrics.totalDecisions = static_cast<int>(decisions.size());
    metrics.executedTrades = static_cast<int>(trades.size());

    for (const auto& decision : decisions) {
        if (decision.decision == DecisionType::ACCEPTED) {
            metrics.acceptedTrades++;
        } else {
            metrics.rejectedSetups++;
        }
    }

    if (!trades.empty()) {
        metrics.totalPnl = std::accumulate(
            trades.begin(),
            trades.end(),
            0.0,
            [](double sum, const TradeResult& trade) {
                return sum + trade.pnl;
            }
        );

        int wins = 0;
        metrics.bestTrade = trades.front().pnl;
        metrics.worstTrade = trades.front().pnl;

        for (const auto& trade : trades) {
            if (trade.pnl > 0) wins++;
            metrics.bestTrade = std::max(metrics.bestTrade, trade.pnl);
            metrics.worstTrade = std::min(metrics.worstTrade, trade.pnl);
        }

        metrics.winRate = static_cast<double>(wins) / static_cast<double>(trades.size()) * 100.0;
        metrics.averagePnl = metrics.totalPnl / static_cast<double>(trades.size());
    }

    if (!equityCurve.empty()) {
        metrics.endingEquity = equityCurve.back();

        double peak = equityCurve.front();
        double maxDd = 0.0;

        for (double equity : equityCurve) {
            peak = std::max(peak, equity);
            double drawdown = peak > 0 ? (equity - peak) / peak : 0.0;
            maxDd = std::min(maxDd, drawdown);
        }

        metrics.maxDrawdown = maxDd * 100.0;
    }

    return metrics;
}
