#include "RiskEngine.hpp"
#include <algorithm>
#include <cmath>

RiskEngine::RiskEngine(RiskConfig config) : config_(config) {}

TradeDecision RiskEngine::evaluate(
    const Candle& candle,
    const Signal& signal,
    double realizedDailyPnl,
    double currentPortfolioExposure,
    const std::unordered_map<std::string, double>& currentSymbolExposure
) const {
    TradeDecision decision;
    decision.timestamp = candle.timestamp;
    decision.symbol = candle.symbol;
    decision.signal = signal.type;
    decision.entryPrice = candle.close;

    if (signal.type == SignalType::NONE) {
        decision.reasonCode = DecisionReasonCode::NO_SIGNAL;
        decision.reason = signal.reason;
        return decision;
    }

    double maxDailyLoss = config_.accountEquity * config_.maxDailyLossPct;
    if (realizedDailyPnl <= -maxDailyLoss) {
        decision.reasonCode = DecisionReasonCode::MAX_DAILY_LOSS;
        decision.reason = "Rejected: max daily loss reached";
        return decision;
    }

    double stopDistance = candle.close * config_.stopLossPct;
    if (stopDistance <= 0) {
        decision.reasonCode = DecisionReasonCode::INVALID_STOP_DISTANCE;
        decision.reason = "Rejected: invalid stop distance";
        return decision;
    }

    double riskBudget = config_.accountEquity * config_.maxRiskPerTradePct;
    int quantity = static_cast<int>(riskBudget / stopDistance);

    double maxNotional = config_.accountEquity * config_.maxPositionValuePct;
    int maxQuantityByNotional = static_cast<int>(maxNotional / candle.close);
    quantity = std::min(quantity, maxQuantityByNotional);

    if (quantity <= 0) {
        decision.reasonCode = DecisionReasonCode::POSITION_TOO_SMALL;
        decision.reason = "Rejected: position size too small under risk limits";
        return decision;
    }

    double proposedNotional = quantity * candle.close;

    double maxPortfolioExposure = config_.accountEquity * config_.maxPortfolioExposurePct;
    if (currentPortfolioExposure + proposedNotional > maxPortfolioExposure) {
        decision.reasonCode = DecisionReasonCode::PORTFOLIO_EXPOSURE_LIMIT;
        decision.reason = "Rejected: portfolio exposure limit exceeded";
        return decision;
    }

    double maxSymbolExposure = config_.accountEquity * config_.maxSymbolExposurePct;
    double symbolExposure = 0.0;

    auto it = currentSymbolExposure.find(candle.symbol);
    if (it != currentSymbolExposure.end()) {
        symbolExposure = it->second;
    }

    if (symbolExposure + proposedNotional > maxSymbolExposure) {
        decision.reasonCode = DecisionReasonCode::SYMBOL_EXPOSURE_LIMIT;
        decision.reason = "Rejected: symbol exposure limit exceeded";
        return decision;
    }

    decision.quantity = quantity;
    decision.riskDollars = quantity * stopDistance;
    decision.notionalValue = proposedNotional;

    if (signal.type == SignalType::LONG) {
        decision.stopLoss = candle.close * (1.0 - config_.stopLossPct);
        decision.takeProfit = candle.close * (1.0 + config_.takeProfitPct);
    } else {
        decision.stopLoss = candle.close * (1.0 + config_.stopLossPct);
        decision.takeProfit = candle.close * (1.0 - config_.takeProfitPct);
    }

    decision.decision = DecisionType::ACCEPTED;
    decision.reasonCode = DecisionReasonCode::TRADE_ACCEPTED;
    decision.reason = "Accepted: " + signal.reason;
    return decision;
}
