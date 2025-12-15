# Real-Life Prompt Gallery

Use these ready-to-run prompts in ChatGPT/Claude to drive the FCCS MCP Agentic Server. Replace bracketed values with your context.

## Health & Connectivity
- "Check FCCS connectivity and show the application info."
- "List available tools and give a one-line purpose for each."
- "Run a health check on the web API and return the status."

## Data Retrieval & Analysis
- "Get FCCS_Net Income for Entity `[Entity]` for FY25 YTD and summarize variances vs FY24."
- "Export a data slice for Account `FCCS_Gross Profit`, Entity `[Entity]`, Scenario Actual, Year FY25, Period Dec."
- "Smart retrieve AP and AR balances for `[Entity]` FY25 YTD and show top 5 largest movements."
- "Get CTA (cumulative translation adjustment) for FY25 and highlight entities with largest FX impact."

## Performance Insights
- "Show the top 10 performers by Net Income for FY25 and include the total."
- "List the bottom 10 entities by Net Income for FY25 with a brief risk note per entity."
- "Summarize YTD vs prior-year performance for `[Entity]` with key drivers."

## Journals & Close
- "List open journals for period Dec FY25 and show status, preparer, and amount."
- "Get details for journal `[Journal Label]` including line items and status."
- "Approve journal `[Journal Label]` and then post it if it is in `Submitted` status."

## Jobs & Automations
- "List the most recent 20 jobs and their status."
- "Check job status for job ID `[ID]` and summarize duration and errors."
- "Run the Consolidation business rule for Scenario Actual, Year FY25, Period Dec."

## Metadata & Dimensions
- "List members in the `Entity` dimension under `[Parent]` (depth 3)."
- "Show the hierarchy path for member `[Entity]` in Entity dimension."
- "Export consolidation rulesets and save them locally."

## Reports
- "Generate the Enterprise Journal report for Actual FY25 Dec as PDF and provide the download link."
- "Generate an intercompany matching report and summarize unmatched pairs."

## Data Operations (use with caution)
- "Copy data from Scenario Budget FY25 to Scenario Actual FY25 for Period Jan–Mar."
- "Clear data for Scenario Forecast FY25 Period Dec for Entity `[Entity]`."
- "Import supplementation data from file `[path]` and report rows loaded and errors."

## Feedback & Metrics
- "Show tool execution metrics: success rate, avg duration, and top 5 slowest tools."
- "Record user feedback score 5 with note 'Great response quality' for the last action."

## Dashboard & Web
- "Start the performance dashboard and provide the local URL."
- "Run the web API server and confirm the health endpoint responds."

## Troubleshooting
- "Test FCCS connection and return any auth or network errors."
- "Diagnose why Net Income for `[Entity]` is returning null in FY25 and suggest next checks."

## Templates for Fast Reuse
- "For each top 5 entity by Net Income FY25, show Net Income, Gross Profit, and Operating Expenses with variance vs FY24."
- "List journals in `Submitted` status for FY25 Dec with amounts > 1,000,000 and prepare approval commands."
- "Export a grid: Scenario Actual, Year FY25, Period Dec, Entities `[E1, E2, E3]`, Accounts `[A1, A2, A3]`, in CSV."

