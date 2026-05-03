#pragma once

#include "Types.hpp"

class RiskEngine {
public:
    explicit RiskEngine(RiskConfig config);

    TradeDecision evaluate(const Candle& candle, const Signal& signal, double realizedDailyPnl) const;

private:
    RiskConfig config_;
};
