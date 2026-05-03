#pragma once

#include "Types.hpp"
#include <string>
#include <unordered_map>

class RiskEngine {
public:
    explicit RiskEngine(RiskConfig config);

    TradeDecision evaluate(
        const Candle& candle,
        const Signal& signal,
        double realizedDailyPnl,
        double currentPortfolioExposure = 0.0,
        const std::unordered_map<std::string, double>& currentSymbolExposure = {}
    ) const;

private:
    RiskConfig config_;
};
