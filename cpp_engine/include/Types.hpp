#pragma once

#include <string>
#include <vector>

enum class SignalType {
    NONE,
    LONG,
    SHORT
};

enum class DecisionType {
    ACCEPTED,
    REJECTED
};

struct Tick {
    std::string timestamp;
    double price{};
    double volume{};
};

struct Candle {
    std::string timestamp;
    double open{};
    double high{};
    double low{};
    double close{};
    double volume{};
};

struct Signal {
    SignalType type{SignalType::NONE};
    std::string reason;
    double confidence{};
};

struct RiskConfig {
    double accountEquity{10000.0};
    double maxRiskPerTradePct{0.01};
    double maxDailyLossPct{0.03};
    double maxPositionValuePct{0.25};
    double stopLossPct{0.004};
    double takeProfitPct{0.008};
};

struct TradeDecision {
    std::string timestamp;
    DecisionType decision{DecisionType::REJECTED};
    SignalType signal{SignalType::NONE};
    std::string reason;
    double entryPrice{};
    double stopLoss{};
    double takeProfit{};
    int quantity{};
    double riskDollars{};
    double notionalValue{};
};

struct TradeResult {
    std::string timestamp;
    SignalType side{SignalType::NONE};
    double entryPrice{};
    double exitPrice{};
    int quantity{};
    double pnl{};
    std::string exitReason;
};
