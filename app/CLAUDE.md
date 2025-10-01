# 🦑 Squber - Squid Catchers AI Assistant

## Proposal: AI Assistant for Squid Fishers

### (1) Issue

Squid fishing is a massive global industry that is highly perishable, energy-intensive, and volatile. Captains face constant uncertainty:

- **Where & when to fish** – migrations shift with temperature, currents, moon phase
- **Fuel costs** – boats burn significant fuel searching
- **Catch variability** – trips swing between highly productive and empty
- **Market timing** – prices fluctuate daily based on landings and freshness
- **Knowledge gap** – global demand signals (festivals, exports, quota changes) are opaque to most crews

The result: **missed opportunities, wasted catch, and unstable incomes.**

### (2) Target Users

- **Phase 1**: Industrial squid seiners and jigging fleets
- **Phase 2**: Other large fisheries with similar volatility
- **Phase 3**: Adjacent maritime markets (processors, exporters)

### (3) Solution Summary

We propose an **AI chatbot agent** that helps captains answer three key questions:

1. **When should I leave port?**
2. **When should I return?**
3. **Which port should I land in?**

The agent uses LLMs and data integrations (market, regulatory, fleet, seasonality) to forecast conditions and translate them into plain-language recommendations. Captains can plan on shore and adjust at sea with local offline models, syncing when connectivity is available (e.g., Starlink).

### (4) Differentiation

- **Focused on market intelligence**, not vessel operations
- **Built for maritime realities**: offline-first, rugged Android devices, glove-friendly voice interface
- **Simplifies statistical complexity** into actionable advice, reducing reliance on guesswork
- **Designed with trust in mind**: privacy-respecting, minimal cost-shifting, transparent explanations

### (5) KPIs

- **Trajectory comparison**: simulated earnings with vs. without agent input
- **Market benchmark**: average earnings of users vs. non-users

### (6) MVP Scope

- **Android chatbot prototype**
- **Tool calls to synthetic market + regulatory datasets**
- **Offline-first architecture** with sync capability
- **Demo scenario**: "Without AI vs. With AI" showing potential revenue uplift

### (7) Architecture Sketch

```
[Data Sources] → [Central Data Service] → [MCP Server] → [Chatbot Interface] → [LLM Provider]
```

**Tools:**
- `get_market_report` (market/regulatory events)
- `query_data` (unified tables)
- `trip_advisor` (trip planning recommendations)
- `squber_howto` (database schema and examples)

### (8) Data Plan

- **Market & landings**: PacFIN (historical prices), synthetic auction data
- **Regulations**: CDFW bulletins, quota closures
- **Fleet activity**: AIS traffic (mocked)
- **Demand signals**: holidays, exports, processing plant capacity (synthetic)
- **Demo data**: NOAA public sets + generated catch logs

### (9) Risks

- **Local LLMs may lack power**; fallback to remote providers
- **Harsh environment may make chatbot use difficult**; solved with voice mode + rugged devices
- **Connectivity gaps**; addressed with offline-first design
- **Adoption depends on measurable economic value**; KPI tracking will test this

---

## Current Implementation Status

This MCP server implements the **data integration layer** of the Squber system, providing:

### 🗄️ Maritime Database
- **7 specialized tables** with 3,320+ records
- **Realistic squid fishing data**: ports, prices, regulations, fleet activity
- **90 days of market data** with seasonal pricing patterns
- **Active regulatory compliance** tracking

### 🛠️ FastMCP Tools

#### `get_market_report(days, port_codes)`
**Answers: "Which port should I land in?"**
- Current market conditions and price trends
- Port comparison with recommendations
- Active regulations affecting operations
- Demand signals and market outlook

#### `trip_advisor(vessel_name, target_port)`
**Answers: "When should I leave/return?"**
- Trip planning recommendations
- Market timing advice
- Regulatory alerts (weekend closures, etc.)
- Fleet performance insights and hot fishing areas

#### `query_data(query)`
**Direct database access for custom analysis**
- Readonly SQL queries against maritime database
- Flexible data exploration and analysis
- Security: SELECT queries only

#### `squber_howto(table_name)`
**Database guide and schema information**
- Maritime database structure explanation
- Example queries for common captain questions
- Data relationships and available insights

### 📊 Real Data Examples

**Market Intelligence:**
- Monterey: $2.98/lb (Grade A squid, current market leader)
- Supply levels: Low supply driving premium pricing
- Seasonal patterns: Peak season (Nov-Mar) vs off-season rates

**Fleet Performance:**
- Top recent catch: NORTHWIND - 47,314 lbs = $86,949 (Monterey Bay)
- Active fleet: 8 vessels (6 seiners, 2 jiggers)
- Hot fishing areas: Santa Barbara Channel showing recent success

**Regulatory Awareness:**
- Weekend fishing closures (Friday 12:01am - Monday 12:01am)
- Monterey Bay 3-nautical-mile closure zone
- Daily vessel limits: 50 tons maximum
- EEZ restrictions: No lights >1000 watts

### 🚀 Usage

**Start the MCP Server (Local):**
```bash
uv run squber
```

**Start HTTP Server + ngrok (Public):**
```bash
./go.sh
```

**Public MCP Endpoint:**
- **URL**: `https://unmeaningly-nonexpiring-ladonna.ngrok-free.dev/mcp`
- **API Key**: `squid-fishing-captain-2024-secure-key-123`
- **Auth Header**: `X-API-Key`

**Test All Tools:**
```bash
uv run python test_server.py
```

**View Maritime Data:**
```bash
uv run python show_data.py
```

### 🎯 Captain Decision Support

The system helps squid fishing captains make **data-driven decisions** by providing:

1. **Market Intelligence** - Real-time pricing, demand signals, port comparisons
2. **Regulatory Compliance** - Active rules, closures, quota tracking
3. **Fleet Analytics** - Performance insights, successful fishing areas
4. **Trip Planning** - Timing recommendations, route optimization

This MCP server serves as the **foundational data layer** for the complete Squber AI assistant, ready to be integrated with chatbot interfaces and mobile applications for at-sea use.

---

## Two-Week Development Roadmap

| Day | Milestone | Deliverable |
|-----|-----------|-------------|
| Day 0 | Kickoff, data sourcing, repo setup | ✅ Project board, maritime dataset |
| Day 7 | MCP server + chatbot prototype | ✅ Demo: market intelligence + trip recommendations |
| Day 12 | Integrated scenario + polish | 🎯 MVP demo, README, final slides |

**Current Status**: ✅ **Day 7 Complete** - MCP server with maritime data and specialized tools operational

**Next Steps**: Integration with chatbot interface and mobile-friendly deployment for at-sea testing scenarios.