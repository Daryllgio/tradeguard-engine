#pragma once

#include "Types.hpp"
#include "SignalEngine.hpp"
#include "RiskEngine.hpp"
#include <vector>

class Backtester {
public:
    explicit Backtester(RiskConfig config);

    void run(const std::vector<Candle>& candles);

    const std::vector<TradeDecision>& decisions() const;
    const std::vector<TradeResult>& trades() const;
    const std::vector<double>& equityCurve() const;

private:
    RiskConfig config_;
    SignalEngine signalEngine_;
    RiskEngine riskEngine_;

    std::vector<TradeDecision> decisions_;
    std::vector<TradeResult> trades_;
    std::vector<double> equityCurve_;

    TradeResult simulateTrade(const std::vector<Candle>& candles, size_t entryIndex, const TradeDecision& decision) const;
};
