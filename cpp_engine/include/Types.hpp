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

enum class DecisionReasonCode {
    TRADE_ACCEPTED,
    NO_SIGNAL,
    MAX_DAILY_LOSS,
    INVALID_STOP_DISTANCE,
    POSITION_TOO_SMALL,
    SYMBOL_EXPOSURE_LIMIT,
    PORTFOLIO_EXPOSURE_LIMIT
};

struct Tick {
    std::string timestamp;
    std::string symbol;
    double price{};
    double volume{};
};

struct Candle {
    std::string timestamp;
    std::string symbol;
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
    double maxSymbolExposurePct{0.35};
    double maxPortfolioExposurePct{0.75};
    double stopLossPct{0.004};
    double takeProfitPct{0.008};
    double slippagePct{0.0005};
    double commissionPerTrade{0.0};
};

struct TradeDecision {
    std::string timestamp;
    std::string symbol;
    DecisionType decision{DecisionType::REJECTED};
    DecisionReasonCode reasonCode{DecisionReasonCode::NO_SIGNAL};
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
    std::string symbol;
    SignalType side{SignalType::NONE};
    double entryPrice{};
    double exitPrice{};
    int quantity{};
    double pnl{};
    std::string exitReason;
    size_t exitIndex{};
};
