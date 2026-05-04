import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Cpu,
  Database,
  GitBranch,
  LayoutDashboard,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Square,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_BASE = "http://localhost:8000";

type Page = "overview" | "live" | "risk" | "strategy" | "trades" | "system";

type Summary = {
  total_decisions: number;
  accepted_trades: number;
  rejected_setups: number;
  executed_trades: number;
  ending_equity: number;
  total_pnl: number;
  win_rate: number;
  average_pnl: number;
  best_trade: number;
  worst_trade: number;
  max_drawdown: number;
};

type DecisionRow = {
  timestamp: string;
  symbol: string;
  decision: string;
  reason_code: string;
  signal: string;
  notional_value: number;
  entry_price: number;
  quantity: number;
};

type TradeRow = {
  timestamp: string;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  exit_reason: string;
};

type OptimizationRow = {
  run: string;
  total_pnl: number;
  ending_equity: number;
  win_rate: number;
  max_risk_per_trade_pct: number;
  stop_loss_pct: number;
  take_profit_pct: number;
};

type RiskData = {
  config: Record<string, number>;
  reason_counts: Record<string, number>;
  symbol_exposure: Record<string, number>;
  total_rejections: number;
};

type LiveStatus = {
  running: boolean;
  mode: string;
  broker: string;
  last_started_at: string | null;
  last_run_at: string | null;
};

type BrokerAccount = {
  simulated?: Record<string, unknown>;
  alpaca?: {
    adapter?: string;
    mode?: string;
    configured?: boolean;
    message?: string;
    account_number?: string;
    status?: string;
    currency?: string;
    cash?: number;
    portfolio_value?: number;
    buying_power?: number;
    equity?: number;
    paper?: boolean;
  };
};

type BrokerOrders = {
  adapter: string;
  configured: boolean;
  orders: Array<Record<string, unknown>>;
};


const fallbackSummary: Summary = {
  total_decisions: 0,
  accepted_trades: 0,
  rejected_setups: 0,
  executed_trades: 0,
  ending_equity: 10000,
  total_pnl: 0,
  win_rate: 0,
  average_pnl: 0,
  best_trade: 0,
  worst_trade: 0,
  max_drawdown: 0,
};

async function apiGet<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) return fallback;
    return response.json();
  } catch {
    return fallback;
  }
}

async function apiPost<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, { method: "POST" });
    if (!response.ok) return fallback;
    return response.json();
  } catch {
    return fallback;
  }
}

function money(value: number | string) {
  const number = Number(value || 0);
  return number.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

function percent(value: number | string) {
  return `${Number(value || 0).toFixed(2)}%`;
}

function App() {
  const [page, setPage] = useState<Page>("overview");
  const [summary, setSummary] = useState<Summary>(fallbackSummary);
  const [decisions, setDecisions] = useState<DecisionRow[]>([]);
  const [trades, setTrades] = useState<TradeRow[]>([]);
  const [optimization, setOptimization] = useState<OptimizationRow[]>([]);
  const [risk, setRisk] = useState<RiskData>({
    config: {},
    reason_counts: {},
    symbol_exposure: {},
    total_rejections: 0,
  });
  const [benchmark, setBenchmark] = useState("");
  const [brokerAccount, setBrokerAccount] = useState<BrokerAccount>({});
  const [brokerOrders, setBrokerOrders] = useState<BrokerOrders>({
    adapter: "AlpacaBrokerAdapter",
    configured: false,
    orders: [],
  });
  const [liveStatus, setLiveStatus] = useState<LiveStatus>({
    running: false,
    mode: "SIMULATED_PAPER",
    broker: "SimulatedBrokerAdapter",
    last_started_at: null,
    last_run_at: null,
  });
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState("Connecting");

  const [symbolFilter, setSymbolFilter] = useState("ALL");
  const [decisionFilter, setDecisionFilter] = useState("ALL");
  const [reasonFilter, setReasonFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  async function loadData() {
    const [
      summaryData,
      decisionsData,
      tradesData,
      optimizationData,
      benchmarkData,
      riskData,
      liveData,
      brokerAccountData,
      brokerOrdersData,
    ] = await Promise.all([
      apiGet<Summary>("/api/summary", fallbackSummary),
      apiGet<DecisionRow[]>("/api/decisions", []),
      apiGet<TradeRow[]>("/api/trades", []),
      apiGet<OptimizationRow[]>("/api/optimization", []),
      apiGet<{ text: string }>("/api/benchmark", { text: "" }),
      apiGet<RiskData>("/api/risk", {
        config: {},
        reason_counts: {},
        symbol_exposure: {},
        total_rejections: 0,
      }),
      apiGet<LiveStatus>("/api/live/status", liveStatus),
      apiGet<BrokerAccount>("/api/broker/account", {}),
      apiGet<BrokerOrders>("/api/broker/orders", {
        adapter: "AlpacaBrokerAdapter",
        configured: false,
        orders: [],
      }),
    ]);

    setSummary(summaryData);
    setDecisions(decisionsData);
    setTrades(tradesData);
    setOptimization(optimizationData);
    setBenchmark(benchmarkData.text);
    setRisk(riskData);
    setLiveStatus(liveData);
    setBrokerAccount(brokerAccountData);
    setBrokerOrders(brokerOrdersData);
    setApiStatus("Connected");
  }

  async function runEngine() {
    setLoading(true);
    const result = await apiPost<{ ok?: boolean }>("/api/run-engine", { ok: false });
    await loadData();
    setApiStatus(result.ok ? "Updated" : "Engine error");
    setLoading(false);
  }

  async function runOptimization() {
    setLoading(true);
    const result = await apiPost<{ ok?: boolean }>("/api/run-optimization", { ok: false });
    await loadData();
    setApiStatus(result.ok ? "Optimization updated" : "Optimization error");
    setLoading(false);
  }

  async function startLive() {
    await apiPost("/api/live/start", {});
    await loadData();
  }

  async function stopLive() {
    await apiPost("/api/live/stop", {});
    await loadData();
  }

  async function submitPaperTestOrder() {
    setLoading(true);

    const result = await apiPost<{ ok?: boolean; message?: string }>("/api/broker/test-order", {
      ok: false,
      message: "Order failed",
    });

    await loadData();

    setApiStatus(result.ok ? "Paper order submitted" : result.message || "Order failed");
    setLoading(false);
  }

  useEffect(() => {
    loadData().catch(() => setApiStatus("API offline"));
  }, []);

  const decisionMix = useMemo(
    () => [
      { name: "Accepted", value: summary.accepted_trades },
      { name: "Rejected", value: summary.rejected_setups },
    ],
    [summary]
  );

  const rejectionData = useMemo(
    () =>
      Object.entries(risk.reason_counts)
        .map(([reason, count]) => ({ reason, count }))
        .sort((a, b) => b.count - a.count),
    [risk]
  );

  const symbolExposureData = useMemo(
    () =>
      Object.entries(risk.symbol_exposure).map(([symbol, exposure]) => ({
        symbol,
        exposure,
      })),
    [risk]
  );

  const symbolPnlData = useMemo(() => {
    const grouped = trades.reduce<Record<string, { symbol: string; pnl: number; trades: number }>>(
      (acc, row) => {
        if (!acc[row.symbol]) {
          acc[row.symbol] = { symbol: row.symbol, pnl: 0, trades: 0 };
        }
        acc[row.symbol].pnl += Number(row.pnl || 0);
        acc[row.symbol].trades += 1;
        return acc;
      },
      {}
    );

    return Object.values(grouped);
  }, [trades]);

  const equityCurve = useMemo(() => {
    let equity = 10000;
    return trades.map((trade, index) => {
      equity += Number(trade.pnl || 0);
      return { step: index + 1, equity: Number(equity.toFixed(2)) };
    });
  }, [trades]);

  const symbols = useMemo(() => {
    return Array.from(new Set(decisions.map((row) => row.symbol).filter(Boolean))).sort();
  }, [decisions]);

  const reasonCodes = useMemo(() => {
    return Array.from(new Set(decisions.map((row) => row.reason_code).filter(Boolean))).sort();
  }, [decisions]);

  const filteredDecisions = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return decisions.filter((row) => {
      const matchesSymbol = symbolFilter === "ALL" || row.symbol === symbolFilter;
      const matchesDecision = decisionFilter === "ALL" || row.decision === decisionFilter;
      const matchesReason = reasonFilter === "ALL" || row.reason_code === reasonFilter;

      const searchable = [
        row.timestamp,
        row.symbol,
        row.decision,
        row.reason_code,
        row.signal,
        String(row.notional_value ?? ""),
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchable.includes(query);

      return matchesSymbol && matchesDecision && matchesReason && matchesSearch;
    });
  }, [decisions, symbolFilter, decisionFilter, reasonFilter, searchQuery]);

  const filteredTrades = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return trades.filter((row) => {
      const matchesSymbol = symbolFilter === "ALL" || row.symbol === symbolFilter;

      const searchable = [
        row.timestamp,
        row.symbol,
        row.side,
        row.exit_reason,
        String(row.pnl ?? ""),
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchable.includes(query);

      return matchesSymbol && matchesSearch;
    });
  }, [trades, symbolFilter, searchQuery]);

  const latestDecisions = filteredDecisions.slice(0, 12);
  const topOptimization = optimization.filter((row) => row.run).slice(0, 10);

  const nav = [
    { id: "overview", label: "Overview", icon: <LayoutDashboard size={17} /> },
    { id: "live", label: "Live Engine", icon: <Activity size={17} /> },
    { id: "risk", label: "Risk Center", icon: <ShieldCheck size={17} /> },
    { id: "strategy", label: "Strategy Lab", icon: <GitBranch size={17} /> },
    { id: "trades", label: "Trade Blotter", icon: <Database size={17} /> },
    { id: "system", label: "System", icon: <Cpu size={17} /> },
  ] as const;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">TG</div>
          <div>
            <h1>TradeGuard</h1>
            <p>Trading risk platform</p>
          </div>
        </div>

        <nav className="nav">
          {nav.map((item) => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={page === item.id ? "active" : ""}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="broker-card">
          <p>Broker Mode</p>
          <strong>{liveStatus.mode}</strong>
          <span>{liveStatus.broker}</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">C++20 · Python FastAPI · React TypeScript</p>
            <h2>{nav.find((item) => item.id === page)?.label}</h2>
          </div>

          <div className="actions">
            <span className="status">{apiStatus}</span>
            <button onClick={loadData} className="secondary">
              <RefreshCw size={15} />
              Refresh
            </button>
            <button onClick={runEngine} disabled={loading}>
              <Play size={15} />
              {loading ? "Running..." : "Run Engine"}
            </button>
          </div>
        </header>

        {page === "overview" && (
          <>
            <section className="hero">
              <div>
                <p className="section-label">Latest run</p>
                <h3>Multi-symbol paper-trading risk analytics.</h3>
                <p>
                  The dashboard is powered by FastAPI endpoints that read outputs generated
                  by the C++ risk engine and Python analytics layer.
                </p>
              </div>

              <div className="hero-kpis">
                <div>
                  <span>Total PnL</span>
                  <strong>{money(summary.total_pnl)}</strong>
                </div>
                <div>
                  <span>Win Rate</span>
                  <strong>{percent(summary.win_rate)}</strong>
                </div>
              </div>
            </section>

            <MetricGrid summary={summary} />

            <section className="grid two">
              <ChartCard title="Decision Mix" subtitle="Accepted versus rejected decisions.">
                <ResponsiveContainer width="100%" height={210}>
                  <BarChart data={decisionMix}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="name" fontSize={12} stroke="#64748b" />
                    <YAxis fontSize={12} stroke="#64748b" />
                    <Tooltip />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {decisionMix.map((entry) => (
                        <Cell
                          key={entry.name}
                          fill={entry.name === "Accepted" ? "#16a34a" : "#dc2626"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Equity Curve" subtitle="Portfolio equity across executed trades.">
                <ResponsiveContainer width="100%" height={210}>
                  <LineChart data={equityCurve}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="step" fontSize={12} stroke="#64748b" />
                    <YAxis fontSize={12} stroke="#64748b" domain={["auto", "auto"]} />
                    <Tooltip formatter={(value) => money(Number(value))} />
                    <Line
                      type="monotone"
                      dataKey="equity"
                      stroke="#2563eb"
                      strokeWidth={2.5}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            </section>
          </>
        )}

        {page === "live" && (
          <>
            <section className="hero compact">
              <div>
                <p className="section-label">Simulated paper mode</p>
                <h3>{liveStatus.running ? "Engine is marked running." : "Engine is currently stopped."}</h3>
                <p>
                  This mode simulates a broker-controlled trading workflow. The Alpaca adapter
                  is planned but not enabled until paper API keys are configured.
                </p>
              </div>

              <div className="live-controls">
                <button onClick={startLive}>
                  <Play size={15} />
                  Start Simulation
                </button>
                <button onClick={stopLive} className="danger">
                  <Square size={15} />
                  Stop
                </button>
              </div>
            </section>

            <section className="grid two">
              <InfoCard label="Broker Adapter" value={liveStatus.broker} />
              <InfoCard label="Last Engine Run" value={liveStatus.last_run_at || "Not run yet"} />
            </section>

            <section className="panel">
              <div className="panel-heading centered">
                <h3>Alpaca Paper Account</h3>
                <p>Real Alpaca paper-trading account data from the connected broker API.</p>
              </div>

              <div className="broker-grid">
                <InfoCard
                  label="Configured"
                  value={brokerAccount.alpaca?.configured ? "Yes" : "No"}
                />
                <InfoCard
                  label="Portfolio Value"
                  value={money(brokerAccount.alpaca?.portfolio_value || 0)}
                />
                <InfoCard
                  label="Buying Power"
                  value={money(brokerAccount.alpaca?.buying_power || 0)}
                />
                <InfoCard
                  label="Cash"
                  value={money(brokerAccount.alpaca?.cash || 0)}
                />
              </div>

              <div className="broker-actions">
                <button onClick={submitPaperTestOrder} disabled={loading || !brokerAccount.alpaca?.configured}>
                  Submit 1 AAPL Paper Order
                </button>
                <span>
                  {brokerAccount.alpaca?.configured
                    ? `Account ${brokerAccount.alpaca?.account_number || ""} · Orders loaded: ${brokerOrders.orders.length}`
                    : brokerAccount.alpaca?.message || "Alpaca account is not configured."}
                </span>
              </div>
            </section>

            <TableCard title="Latest Engine Decisions" subtitle="Most recent generated decision records.">
              <DecisionTable rows={latestDecisions} />
            </TableCard>
          </>
        )}

        {page === "risk" && (
          <>
            <MetricGrid summary={summary} />

            <FilterPanel
              symbols={symbols}
              reasonCodes={reasonCodes}
              symbolFilter={symbolFilter}
              setSymbolFilter={setSymbolFilter}
              decisionFilter={decisionFilter}
              setDecisionFilter={setDecisionFilter}
              reasonFilter={reasonFilter}
              setReasonFilter={setReasonFilter}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />

            <section className="grid two">
              <ChartCard title="Rejection Reason Codes" subtitle="Why the risk engine rejected trades.">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={rejectionData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis type="number" fontSize={12} stroke="#64748b" />
                    <YAxis
                      type="category"
                      dataKey="reason"
                      width={160}
                      fontSize={11}
                      stroke="#64748b"
                    />
                    <Tooltip />
                    <Bar dataKey="count" fill="#2563eb" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Symbol Exposure" subtitle="Estimated notional exposure by symbol.">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={symbolExposureData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="symbol" fontSize={12} stroke="#64748b" />
                    <YAxis fontSize={12} stroke="#64748b" />
                    <Tooltip formatter={(value) => money(Number(value))} />
                    <Bar dataKey="exposure" fill="#4f46e5" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </section>

            <ConfigPanel config={risk.config} />
          </>
        )}

        {page === "strategy" && (
          <>
            <section className="hero compact">
              <div>
                <p className="section-label">Strategy Lab</p>
                <h3>Parameter search across risk, stop-loss, and take-profit settings.</h3>
                <p>
                  The optimizer runs multiple configurations and ranks the best results using
                  total PnL, equity, win rate, and drawdown.
                </p>
              </div>

              <div className="live-controls">
                <button onClick={runOptimization} disabled={loading}>
                  <GitBranch size={15} />
                  {loading ? "Optimizing..." : "Run Optimization"}
                </button>
              </div>
            </section>

            <TableCard title="Optimization Results" subtitle="Top parameter configurations.">
              <OptimizationTable rows={topOptimization} />
            </TableCard>
          </>
        )}

        {page === "trades" && (
          <>
            <section className="grid two">
              <ChartCard title="Symbol PnL" subtitle="Executed trade PnL by symbol.">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={symbolPnlData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="symbol" fontSize={12} stroke="#64748b" />
                    <YAxis fontSize={12} stroke="#64748b" />
                    <Tooltip formatter={(value) => money(Number(value))} />
                    <Bar dataKey="pnl" fill="#16a34a" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <InfoCard label="Executed Trades" value={summary.executed_trades.toLocaleString()} />
            </section>

            <FilterPanel
              symbols={symbols}
              reasonCodes={reasonCodes}
              symbolFilter={symbolFilter}
              setSymbolFilter={setSymbolFilter}
              decisionFilter={decisionFilter}
              setDecisionFilter={setDecisionFilter}
              reasonFilter={reasonFilter}
              setReasonFilter={setReasonFilter}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />

            <TableCard title="Trade Blotter" subtitle="Executed trades from the latest engine output.">
              <TradeTable rows={filteredTrades.slice(0, 25)} />
            </TableCard>

            <TableCard title="Decision Log" subtitle="Accepted and rejected trading decisions.">
              <DecisionTable rows={filteredDecisions.slice(0, 25)} />
            </TableCard>
          </>
        )}

        {page === "system" && (
          <>
            <section className="grid two">
              <InfoCard label="API Status" value={apiStatus} />
              <InfoCard label="Engine Mode" value={liveStatus.mode} />
            </section>

            <section className="panel">
              <div className="panel-heading centered">
                <Cpu size={18} />
                <h3>Benchmark Report</h3>
                <p>Runtime metrics generated by the C++ benchmark reporter.</p>
              </div>
              <pre>{benchmark || "No benchmark report available."}</pre>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function MetricGrid({ summary }: { summary: Summary }) {
  return (
    <section className="metrics">
      <InfoCard label="Total Decisions" value={summary.total_decisions.toLocaleString()} icon={<Activity size={18} />} />
      <InfoCard label="Executed Trades" value={summary.executed_trades.toLocaleString()} icon={<TrendingUp size={18} />} />
      <InfoCard label="Ending Equity" value={money(summary.ending_equity)} icon={<WalletCards size={18} />} />
      <InfoCard label="Max Drawdown" value={percent(summary.max_drawdown)} icon={<ShieldCheck size={18} />} />
    </section>
  );
}

function InfoCard({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <article className="info-card">
      <div className="info-icon">{icon || <Activity size={18} />}</div>
      <p>{label}</p>
      <h3>{value}</h3>
    </article>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <article className="panel">
      <div className="panel-heading centered">
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      {children}
    </article>
  );
}

function TableCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-heading centered">
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <div className="table-wrap">{children}</div>
    </section>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="empty-state">
      <Database size={20} />
      <p>{message}</p>
    </div>
  );
}

function FilterPanel({
  symbols,
  reasonCodes,
  symbolFilter,
  setSymbolFilter,
  decisionFilter,
  setDecisionFilter,
  reasonFilter,
  setReasonFilter,
  searchQuery,
  setSearchQuery,
}: {
  symbols: string[];
  reasonCodes: string[];
  symbolFilter: string;
  setSymbolFilter: (value: string) => void;
  decisionFilter: string;
  setDecisionFilter: (value: string) => void;
  reasonFilter: string;
  setReasonFilter: (value: string) => void;
  searchQuery: string;
  setSearchQuery: (value: string) => void;
}) {
  return (
    <section className="filter-panel">
      <div className="search-box">
        <Search size={15} />
        <input
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Search symbol, reason code, signal, timestamp..."
        />
      </div>

      <select value={symbolFilter} onChange={(event) => setSymbolFilter(event.target.value)}>
        <option value="ALL">All symbols</option>
        {symbols.map((symbol) => (
          <option key={symbol} value={symbol}>
            {symbol}
          </option>
        ))}
      </select>

      <select value={decisionFilter} onChange={(event) => setDecisionFilter(event.target.value)}>
        <option value="ALL">All decisions</option>
        <option value="ACCEPTED">Accepted</option>
        <option value="REJECTED">Rejected</option>
      </select>

      <select value={reasonFilter} onChange={(event) => setReasonFilter(event.target.value)}>
        <option value="ALL">All reason codes</option>
        {reasonCodes.map((reason) => (
          <option key={reason} value={reason}>
            {reason}
          </option>
        ))}
      </select>

      <button
        className="clear-filters"
        onClick={() => {
          setSymbolFilter("ALL");
          setDecisionFilter("ALL");
          setReasonFilter("ALL");
          setSearchQuery("");
        }}
      >
        Clear
      </button>
    </section>
  );
}

function DecisionTable({ rows }: { rows: DecisionRow[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Symbol</th>
          <th>Decision</th>
          <th>Reason Code</th>
          <th>Signal</th>
          <th>Notional</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={6}>
              <EmptyState message="No decision records match the current filters." />
            </td>
          </tr>
        )}

        {rows.map((row, index) => (
          <tr key={`${row.timestamp}-${row.symbol}-${index}`}>
            <td>{row.timestamp}</td>
            <td>{row.symbol}</td>
            <td>
              <span className={`badge ${row.decision.toLowerCase()}`}>
                {row.decision}
              </span>
            </td>
            <td>{row.reason_code}</td>
            <td>{row.signal}</td>
            <td>{money(row.notional_value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TradeTable({ rows }: { rows: TradeRow[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Symbol</th>
          <th>Side</th>
          <th>Entry</th>
          <th>Exit</th>
          <th>Qty</th>
          <th>PnL</th>
          <th>Exit Reason</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={6}>
              <EmptyState message="No decision records match the current filters." />
            </td>
          </tr>
        )}

        {rows.map((row, index) => (
          <tr key={`${row.timestamp}-${row.symbol}-${index}`}>
            <td>{row.timestamp}</td>
            <td>{row.symbol}</td>
            <td>{row.side}</td>
            <td>{money(row.entry_price)}</td>
            <td>{money(row.exit_price)}</td>
            <td>{row.quantity}</td>
            <td>{money(row.pnl)}</td>
            <td>{row.exit_reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function OptimizationTable({ rows }: { rows: OptimizationRow[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Run</th>
          <th>Total PnL</th>
          <th>Ending Equity</th>
          <th>Win Rate</th>
          <th>Risk / Trade</th>
          <th>Stop</th>
          <th>Take</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.run}>
            <td>{row.run}</td>
            <td>{money(row.total_pnl)}</td>
            <td>{money(row.ending_equity)}</td>
            <td>{percent(row.win_rate)}</td>
            <td>{row.max_risk_per_trade_pct}</td>
            <td>{row.stop_loss_pct}</td>
            <td>{row.take_profit_pct}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ConfigPanel({ config }: { config: Record<string, number> }) {
  return (
    <section className="panel">
      <div className="panel-heading centered">
        <h3>Risk Configuration</h3>
        <p>Current config loaded from risk_config.json.</p>
      </div>

      <div className="config-grid">
        {Object.entries(config).map(([key, value]) => (
          <div key={key} className="config-item">
            <span>{key}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

export default App;
