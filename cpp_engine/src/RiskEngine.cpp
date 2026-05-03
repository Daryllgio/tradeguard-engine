#include "RiskEngine.hpp"
#include <algorithm>
#include <cmath>

RiskEngine::RiskEngine(RiskConfig config) : config_(config) {}

TradeDecision RiskEngine::evaluate(const Candle& candle, const Signal& signal, double realizedDailyPnl) const {
    TradeDecision decision;
    decision.timestamp = candle.timestamp;
    decision.signal = signal.type;
    decision.entryPrice = candle.close;

    if (signal.type == SignalType::NONE) {
        decision.reason = signal.reason;
        return decision;
    }

    double maxDailyLoss = config_.accountEquity * config_.maxDailyLossPct;
    if (realizedDailyPnl <= -maxDailyLoss) {
        decision.reason = "Rejected: max daily loss reached";
        return decision;
    }

    double stopDistance = candle.close * config_.stopLossPct;
    if (stopDistance <= 0) {
        decision.reason = "Rejected: invalid stop distance";
        return decision;
    }

    double riskBudget = config_.accountEquity * config_.maxRiskPerTradePct;
    int quantity = static_cast<int>(riskBudget / stopDistance);

    double maxNotional = config_.accountEquity * config_.maxPositionValuePct;
    int maxQuantityByNotional = static_cast<int>(maxNotional / candle.close);
    quantity = std::min(quantity, maxQuantityByNotional);

    if (quantity <= 0) {
        decision.reason = "Rejected: position size too small under risk limits";
        return decision;
    }

    decision.quantity = quantity;
    decision.riskDollars = quantity * stopDistance;
    decision.notionalValue = quantity * candle.close;

    if (signal.type == SignalType::LONG) {
        decision.stopLoss = candle.close * (1.0 - config_.stopLossPct);
        decision.takeProfit = candle.close * (1.0 + config_.takeProfitPct);
    } else {
        decision.stopLoss = candle.close * (1.0 + config_.stopLossPct);
        decision.takeProfit = candle.close * (1.0 - config_.takeProfitPct);
    }

    decision.decision = DecisionType::ACCEPTED;
    decision.reason = "Accepted: " + signal.reason;
    return decision;
}
