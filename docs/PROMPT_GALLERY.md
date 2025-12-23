# Real-Life Prompt Gallery

Use these ready-to-run prompts in ChatGPT/Claude to drive the FCCS MCP Agentic Server. Replace bracketed values with your context.

---

## 🏥 Health & Connectivity

### Basic Connectivity
- **"Check FCCS connectivity and show the application info."**
  - *Use case*: Verify server connection and get basic app metadata
  - *Expected*: Application name, version, REST API version, dimensions count

- **"List available tools and give a one-line purpose for each."**
  - *Use case*: Discover what operations are available
  - *Expected*: Complete list of MCP tools with brief descriptions

- **"Run a health check on the web API and return the status."**
  - *Use case*: Verify web server is running
  - *Expected*: HTTP status, response time, service availability

### Advanced Diagnostics
- **"Test FCCS connection and return any auth or network errors."**
  - *Use case*: Troubleshoot connection issues
  - *Expected*: Detailed error messages, authentication status

- **"Get the REST API version and list all available endpoints."**
  - *Use case*: Understand API capabilities
  - *Expected*: API version number and endpoint documentation

---

## 📊 Data Retrieval & Analysis

### Single Account Queries
- **"Get FCCS_Net Income for Entity `[Entity]` for FY25 YTD and summarize variances vs FY24."**
  - *Example*: "Get FCCS_Net Income for Entity `FCCS_Total Geography` for FY25 YTD and summarize variances vs FY24."
  - *Use case*: Quick P&L check for specific entity
  - *Expected*: Current YTD value, prior year comparison, variance analysis

- **"Smart retrieve AP and AR balances for `[Entity]` FY25 YTD and show top 5 largest movements."**
  - *Example*: "Smart retrieve AP and AR balances for `FCCS_US` FY25 YTD and show top 5 largest movements."
  - *Use case*: Balance sheet analysis
  - *Expected*: Account balances with period-over-period changes

- **"Get CTA (cumulative translation adjustment) for FY25 and highlight entities with largest FX impact."**
  - *Use case*: Foreign currency translation analysis
  - *Expected*: CTA values by entity, sorted by magnitude

### Multi-Account Analysis
- **"Export a data slice for Account `FCCS_Gross Profit`, Entity `[Entity]`, Scenario Actual, Year FY25, Period Dec."**
  - *Example*: "Export a data slice for Account `FCCS_Gross Profit`, Entity `FCCS_Europe`, Scenario Actual, Year FY25, Period Dec."
  - *Use case*: Detailed period analysis
  - *Expected*: Grid data with all dimensions specified

- **"For each top 5 entity by Net Income FY25, show Net Income, Gross Profit, and Operating Expenses with variance vs FY24."**
  - *Use case*: Comparative analysis across entities
  - *Expected*: Table with multiple accounts, entities, and variances

- **"Export a grid: Scenario Actual, Year FY25, Period Dec, Entities `[E1, E2, E3]`, Accounts `[A1, A2, A3]`, in CSV."**
  - *Example*: "Export a grid: Scenario Actual, Year FY25, Period Dec, Entities `FCCS_US, FCCS_Europe, FCCS_Asia`, Accounts `FCCS_Revenue, FCCS_COGS, FCCS_Net Income`, in CSV."
  - *Use case*: Custom data extraction for reporting
  - *Expected*: Structured data export ready for Excel/Power BI

### Time Series Analysis
- **"Get monthly Net Income for `[Entity]` FY25 and create a trend chart showing seasonality."**
  - *Use case*: Identify seasonal patterns
  - *Expected*: Monthly values with trend analysis

- **"Compare Q1, Q2, Q3, Q4 Net Income for `[Entity]` FY25 vs FY24 and highlight quarters with >10% variance."**
  - *Use case*: Quarterly performance review
  - *Expected*: Quarter-by-quarter comparison with variance flags

---

## 📈 Performance Insights

### Top/Bottom Performers
- **"Show the top 10 performers by Net Income for FY25 and include the total."**
  - *Use case*: Identify best-performing entities
  - *Expected*: Ranked list with Net Income values and grand total

- **"List the bottom 10 entities by Net Income for FY25 with a brief risk note per entity."**
  - *Use case*: Risk assessment and underperformer identification
  - *Expected*: Ranked list with performance metrics and risk indicators

- **"Find entities with Net Income variance >20% vs FY24 and group by region."**
  - *Use case*: Identify significant changes requiring investigation
  - *Expected*: Filtered list grouped by geographic region

### Variance Analysis
- **"Summarize YTD vs prior-year performance for `[Entity]` FY25 with key drivers."**
  - *Example*: "Summarize YTD vs prior-year performance for `FCCS_US` FY25 with key drivers."
  - *Use case*: Management reporting
  - *Expected*: Summary with revenue, cost, and margin drivers

- **"Calculate revenue growth rate for top 5 entities FY25 YTD and rank by growth."**
  - *Use case*: Growth analysis
  - *Expected*: Growth percentages with rankings

- **"Identify accounts with largest absolute variance between Actual and Budget FY25 Dec."**
  - *Use case*: Budget vs actual analysis
  - *Expected*: Accounts sorted by variance magnitude

---

## 📝 Journals & Close

### Journal Listing & Review
- **"List open journals for period Dec FY25 and show status, preparer, and amount."**
  - *Use case*: Month-end close tracking
  - *Expected*: Journal list with status (Draft, Submitted, Approved, Posted), preparer names, and amounts

- **"List journals in `Submitted` status for FY25 Dec with amounts > 1,000,000 and prepare approval commands."**
  - *Use case*: High-value journal review
  - *Expected*: Filtered journal list with ready-to-run approval commands

- **"Get all journals for Entity `[Entity]` FY25 Dec and group by status."**
  - *Use case*: Entity-specific close tracking
  - *Expected*: Journals grouped by status with counts

### Journal Details & Actions
- **"Get details for journal `[Journal Label]` including line items and status."**
  - *Example*: "Get details for journal `JE-2025-12-001` including line items and status."
  - *Use case*: Journal review before approval
  - *Expected*: Full journal details with debit/credit entries, accounts, entities, amounts

- **"Approve journal `[Journal Label]` and then post it if it is in `Submitted` status."**
  - *Example*: "Approve journal `JE-2025-12-001` and then post it if it is in `Submitted` status."
  - *Use case*: Automated journal workflow
  - *Expected*: Status updates and confirmation of actions taken

- **"Update journal `[Journal Label]` period to `[New Period]` and verify the change."**
  - *Use case*: Correct journal period assignment
  - *Expected*: Confirmation of period update

### Journal Export & Import
- **"Export all journals for FY25 Dec in CSV format with line items."**
  - *Use case*: External audit or analysis
  - *Expected*: CSV file with journal headers and line items

- **"Import journals from file `[path]` and report rows loaded and errors."**
  - *Use case*: Bulk journal entry
  - *Expected*: Import summary with success count and error details

---

## ⚙️ Jobs & Automations

### Job Monitoring
- **"List the most recent 20 jobs and their status."**
  - *Use case*: Monitor system activity
  - *Expected*: Job list with type, name, status, start time, duration

- **"Check job status for job ID `[ID]` and summarize duration and errors."**
  - *Example*: "Check job status for job ID `12345` and summarize duration and errors."
  - *Use case*: Track long-running processes
  - *Expected*: Current status, elapsed time, completion percentage, error messages if any

- **"Find all failed jobs in the last 24 hours and list error messages."**
  - *Use case*: System health monitoring
  - *Expected*: Failed job list with timestamps and error details

### Business Rule Execution
- **"Run the Consolidation business rule for Scenario Actual, Year FY25, Period Dec."**
  - *Use case*: Execute month-end consolidation
  - *Expected*: Job ID, status, and execution confirmation

- **"Run the Consolidation business rule asynchronously and monitor until completion."**
  - *Use case*: Long-running consolidation with progress tracking
  - *Expected*: Job ID, periodic status updates, final completion status

- **"Execute Data Management load rule `[Rule Name]` for periods Jan-Mar FY25 with import mode REPLACE."**
  - *Example*: "Execute Data Management load rule `GL_Load` for periods Jan-Mar FY25 with import mode REPLACE."
  - *Use case*: Data import automation
  - *Expected*: Job execution confirmation and data load summary

---

## 🗂️ Metadata & Dimensions

### Dimension Exploration
- **"List members in the `Entity` dimension under `[Parent]` (depth 3)."**
  - *Example*: "List members in the `Entity` dimension under `FCCS_Total Geography` (depth 3)."
  - *Use case*: Understand organizational hierarchy
  - *Expected*: Hierarchical member list with parent-child relationships

- **"Show the hierarchy path for member `[Entity]` in Entity dimension."**
  - *Example*: "Show the hierarchy path for member `FCCS_US` in Entity dimension."
  - *Use case*: Understand member placement in hierarchy
  - *Expected*: Full path from root to member

- **"Get all members of Account dimension and filter for accounts containing 'Revenue'."**
  - *Use case*: Find specific account types
  - *Expected*: Filtered account list

### Dimension Management
- **"Get member `[Member Name]` from dimension `[Dimension]` with all properties."**
  - *Example*: "Get member `FCCS_Net Income` from dimension `Account` with all properties."
  - *Use case*: Member metadata review
  - *Expected*: Member details including aliases, descriptions, properties

- **"Add new member `[Member Name]` to dimension `[Dimension]` under parent `[Parent]`."**
  - *Example*: "Add new member `New_Entity` to dimension `Entity` under parent `FCCS_Total Geography`."
  - *Use case*: Dimension maintenance
  - *Expected*: Confirmation of member creation

### Metadata Export
- **"Export consolidation rulesets and save them locally."**
  - *Use case*: Backup or version control
  - *Expected*: Ruleset export file

- **"Export all Account dimension members to CSV with aliases and descriptions."**
  - *Use case*: Documentation or external analysis
  - *Expected*: CSV file with member metadata

---

## 📄 Reports

### Standard Reports
- **"Generate the Enterprise Journal report for Actual FY25 Dec as PDF and provide the download link."**
  - *Use case*: Month-end reporting
  - *Expected*: PDF report file with download information

- **"Generate an intercompany matching report and summarize unmatched pairs."**
  - *Use case*: Intercompany reconciliation
  - *Expected*: Report file with summary of matched/unmatched transactions

- **"Generate Task Manager report for FY25 Dec and email to `[email@company.com]`."**
  - *Example*: "Generate Task Manager report for FY25 Dec and email to `finance@company.com`."
  - *Use case*: Automated report distribution
  - *Expected*: Report generation confirmation and email notification

### Custom Reports
- **"Generate a custom HTML report showing Net Income by Entity for FY25 YTD with variance analysis."**
  - *Use case*: Custom analysis presentation
  - *Expected*: HTML report file with charts and tables

- **"Create a Python script template for custom FCCS reporting with accounts `[A1, A2, A3]` and entities `[E1, E2, E3]`."**
  - *Example*: "Create a Python script template for custom FCCS reporting with accounts `FCCS_Revenue, FCCS_COGS, FCCS_Net Income` and entities `FCCS_US, FCCS_Europe`."
  - *Use case*: Custom report development
  - *Expected*: Python script file ready for customization

### Report Status & Management
- **"Check status of report job `[Job ID]` and download when complete."**
  - *Use case*: Monitor async report generation
  - *Expected*: Job status updates and download link when ready

---

## 🔄 Data Operations (Use with Caution)

### Data Copy
- **"Copy data from Scenario Budget FY25 to Scenario Actual FY25 for Period Jan–Mar."**
  - *Use case*: Scenario initialization
  - *Expected*: Confirmation of data copied with row counts

- **"Copy Net Income data from FY24 to FY25 for all entities in Period Dec."**
  - *Use case*: Prior year data seeding
  - *Expected*: Copy operation summary

### Data Clear
- **"Clear data for Scenario Forecast FY25 Period Dec for Entity `[Entity]`."**
  - *Example*: "Clear data for Scenario Forecast FY25 Period Dec for Entity `FCCS_US`."
  - *Use case*: Reset forecast data
  - *Expected*: Confirmation of data cleared

- **"Clear all data for Scenario `[Scenario]` Year `[Year]` Period `[Period]` and confirm."**
  - *Use case*: Complete scenario reset
  - *Expected*: Clear operation confirmation with safety checks

### Data Import
- **"Import supplementation data from file `[path]` and report rows loaded and errors."**
  - *Example*: "Import supplementation data from file `C:\Data\supplement.csv` and report rows loaded and errors."
  - *Use case*: Bulk data load
  - *Expected*: Import summary with success/error counts

---

## 📊 Feedback & Metrics

### Performance Metrics
- **"Show tool execution metrics: success rate, avg duration, and top 5 slowest tools."**
  - *Use case*: System performance monitoring
  - *Expected*: Metrics dashboard with statistics

- **"Get feedback scores for the last 10 tool executions and show average rating."**
  - *Use case*: Quality monitoring
  - *Expected*: Feedback summary with ratings and comments

### User Feedback
- **"Record user feedback score 5 with note 'Great response quality' for the last action."**
  - *Use case*: Improve system through feedback
  - *Expected*: Confirmation of feedback recorded

- **"Show all feedback entries for tool `[Tool Name]` in the last 30 days."**
  - *Use case*: Tool-specific quality analysis
  - *Expected*: Feedback list with scores and comments

---

## 🖥️ Dashboard & Web

### Dashboard Operations
- **"Start the performance dashboard and provide the local URL."**
  - *Use case*: Launch monitoring dashboard
  - *Expected*: Dashboard URL (typically http://localhost:8050)

- **"Open the dashboard and show me the current tool execution statistics."**
  - *Use case*: Real-time monitoring
  - *Expected*: Dashboard access with live metrics

### Web API
- **"Run the web API server and confirm the health endpoint responds."**
  - *Use case*: API server startup verification
  - *Expected*: Server URL and health check response

- **"Test all web API endpoints and return status codes."**
  - *Use case*: API health check
  - *Expected*: Endpoint list with HTTP status codes

---

## 🔧 Troubleshooting

### Connection Issues
- **"Test FCCS connection and return any auth or network errors."**
  - *Use case*: Diagnose connectivity problems
  - *Expected*: Detailed error messages and connection status

- **"Verify authentication credentials and test API access."**
  - *Use case*: Auth troubleshooting
  - *Expected*: Authentication status and token validity

### Data Issues
- **"Diagnose why Net Income for `[Entity]` is returning null in FY25 and suggest next checks."**
  - *Example*: "Diagnose why Net Income for `FCCS_US` is returning null in FY25 and suggest next checks."
  - *Use case*: Data quality investigation
  - *Expected*: Diagnostic steps and potential root causes

- **"Check if consolidation has been run for FY25 Dec and list any errors."**
  - *Use case*: Close process verification
  - *Expected*: Consolidation status and error log

### Validation
- **"Validate application metadata and generate a log file with any issues."**
  - *Use case*: System health check
  - *Expected*: Validation report with issues flagged

---

## 🎯 Templates for Fast Reuse

### Multi-Entity Analysis
- **"For each top 5 entity by Net Income FY25, show Net Income, Gross Profit, and Operating Expenses with variance vs FY24."**
  - *Use case*: Executive summary
  - *Expected*: Comparative table with key metrics

### Journal Workflow
- **"List journals in `Submitted` status for FY25 Dec with amounts > 1,000,000 and prepare approval commands."**
  - *Use case*: High-value journal review workflow
  - *Expected*: Filtered list with ready-to-execute commands

### Custom Grid Export
- **"Export a grid: Scenario Actual, Year FY25, Period Dec, Entities `[E1, E2, E3]`, Accounts `[A1, A2, A3]`, in CSV."**
  - *Example*: "Export a grid: Scenario Actual, Year FY25, Period Dec, Entities `FCCS_US, FCCS_Europe, FCCS_Asia`, Accounts `FCCS_Revenue, FCCS_COGS, FCCS_Net Income`, in CSV."
  - *Use case*: Custom data extraction
  - *Expected*: CSV file with specified data slice

### Period Comparison
- **"Compare Net Income for `[Entity]` across all periods in FY25 and identify the best and worst performing months."**
  - *Use case*: Period performance analysis
  - *Expected*: Period-by-period comparison with highlights

### Scenario Analysis
- **"Compare Actual vs Budget vs Forecast for Net Income FY25 YTD by Entity and highlight variances >10%."**
  - *Use case*: Multi-scenario analysis
  - *Expected*: Comparative table with variance flags

---

## 💡 Tips & Best Practices

1. **Be Specific**: Include exact member names, periods, and scenarios in your prompts
2. **Use Smart Retrieve**: For single account queries, use `smart_retrieve` for automatic dimension handling
3. **Check Status**: For long-running operations, always check job status before proceeding
4. **Export First**: When in doubt, export data to verify before making changes
5. **Use Filters**: Filter journals and data by status, amount, or date ranges for focused analysis
6. **Async Operations**: Use async mode for large reports or long-running consolidations
7. **Error Handling**: Always check for errors in job status and data operations
8. **Documentation**: Export metadata and rulesets regularly for backup

---

## 🚀 Advanced Scenarios

### Complete Close Process
- **"Execute the month-end close for FY25 Dec: 1) Run consolidation, 2) List all journals, 3) Approve submitted journals, 4) Post approved journals, 5) Generate Enterprise Journal report."**
  - *Use case*: Automated close workflow
  - *Expected*: Step-by-step execution with status updates

### Financial Analysis Package
- **"Create a comprehensive financial analysis for FY25 YTD: top 10 entities by revenue, bottom 5 by profit margin, largest variances vs FY24, and intercompany matching status."**
  - *Use case*: Executive reporting package
  - *Expected*: Multi-section analysis report

### Data Quality Check
- **"Run a data quality check for FY25 Dec: identify entities with zero revenue, accounts with null values, and unbalanced journals."**
  - *Use case*: Pre-close validation
  - *Expected*: Data quality report with issues flagged

---

*Last Updated: 2025-01-15*
*For more information, see README.md and other documentation files.*
