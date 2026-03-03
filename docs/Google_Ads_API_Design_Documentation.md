# Google Ads API — Design Documentation

**Application:** EPI (Electro-PI)

*Note: Screenshots and mockups of the tool are included at the end of this document.*

---

## Company Name

[YOUR COMPANY NAME]

## Business Model

Our company develops and sells EPI, a lead verification and attribution SaaS platform. Our clients are digital marketing agencies and businesses that run Google Ads campaigns to generate leads on their websites. Each client may manage multiple websites and Google Ads accounts.

EPI solves a core problem for these clients: verifying whether the leads Google Ads reports as conversions are actually real, qualified leads. Clients install our first-party JavaScript tracking pixel on their websites, which captures form submissions, validates contact information (email and phone), detects bot traffic, and scores lead quality. EPI then compares the client's verified lead counts against what Google Ads reports to surface discrepancies — showing them their true cost-per-verified-lead versus what the ad platform claims.

## Tool Access/Use

EPI is an externally-facing SaaS product. Our clients (digital marketing agencies and businesses) sign up for accounts, connect their own Google Ads accounts via OAuth, and access their data through our platform.

**Who accesses the tool:**

- **Clients (external users):** Agency owners, media buyers, and account managers at our client companies sign up, connect their Google Ads accounts, and use the dashboard to view lead quality reports, attribution data, and platform comparison metrics. Each client is authenticated via email/password with JWT-based sessions. Clients can only see data from their own Google Ads accounts — strict tenant isolation enforces this.
- **Client teams via Slack:** Clients can install our Slack bot into their own workspace to query their lead stats and comparison data conversationally (e.g., "How many verified leads from Google yesterday?"). The Slack bot is scoped to each client's data only.
- **Our internal team:** As the service provider, our team also uses the platform to review client ad performance data, troubleshoot issues, generate reports, and provide strategic recommendations to clients based on their lead quality and attribution data.

**Data access boundaries:** Each client organization can only see their own Google Ads data. There is no cross-client data sharing. Google Ads data pulled for one client is never visible to any other client. All Google Ads data is stored in our PostgreSQL database with row-level tenant isolation.

**Data usage:** We pull each client's Google Ads campaign performance data (impressions, clicks, conversions, spend) on a daily automated schedule. This data is stored in our database and used exclusively to generate comparison reports for that client — comparing Google's reported conversions against EPI's first-party verified leads for their sites.

## Tool Design

EPI has three components that interact with Google Ads data:

**1. OAuth Connection (One-Time Setup)**

During onboarding, each client connects their own Google Ads account through a standard OAuth 2.0 flow. The client clicks "Connect Google Ads" in the onboarding wizard, is redirected to Google's consent screen, authorizes read-only access to their account, and we store the resulting refresh token securely (encrypted at rest with Fernet symmetric encryption). The Google Ads Customer ID is associated with the client's site.

**2. Daily Automated Data Pull (Read-Only)**

A scheduled job runs once daily at 03:00 UTC. For each client site that has a linked Google Ads account, the job:

- Uses the stored refresh token to obtain a fresh access token
- Queries the Google Ads API for the previous day's campaign performance data
- Stores the results (campaign ID, campaign name, ad group ID, ad group name, conversion action, conversions reported, clicks, impressions, spend) in our `platform_conversions` database table
- A second job at 04:00 UTC compares this data against our first-party verified leads and computes a discrepancy percentage and cost-per-verified-lead

**3. Client-Facing Reporting Dashboard**

The dashboard displays comparison data pulled from our database — it does not query the Google Ads API directly at request time. Authenticated clients can:

- View account-level stats: total leads, verified leads, suspicious leads, junk leads
- See platform comparison: Google's reported conversions vs. EPI's verified leads, discrepancy percentage, and cost-per-verified-lead
- Filter by site, date range, and platform (Google Ads or Meta Ads)
- View individual lead details including quality score, attribution tier, and validation results

Clients can also install our Slack bot in their workspace to query the same data through natural language (e.g., "How many verified leads did we get from Google Ads yesterday?"). The bot is scoped to the requesting client's data only.

## API Services Called

We use the Google Ads API for both **reading** campaign performance data and **writing** changes to campaigns, ads, and bidding based on lead quality insights. Specifically:

**Read operations:**

- **GoogleAdsService** — Execute GAQL (Google Ads Query Language) queries to pull campaign and ad group performance metrics. We query the `campaign`, `ad_group`, and `ad_group_ad` resources to retrieve: `metrics.impressions`, `metrics.clicks`, `metrics.conversions`, `metrics.cost_micros`, along with `campaign.id`, `campaign.name`, `ad_group.id`, `ad_group.name`, and `segments.conversion_action` for a given date range.

- **CustomerService** — List accessible customer accounts after OAuth authorization, so the client can select which Google Ads account to link to each of their sites during onboarding.

**Write operations:**

- **CampaignService** — Create, update, and pause campaigns. For example, pausing campaigns that are generating a high percentage of junk leads or adjusting campaign settings based on lead quality data.

- **AdGroupAdService** — Create, update, and pause ads within ad groups. Enable or disable specific ads based on which creatives are driving verified vs. junk leads.

- **AdGroupService** — Manage ad groups, including pausing ad groups with poor lead quality performance.

- **CampaignBudgetService** — Adjust campaign budgets to reallocate spend toward campaigns producing higher-quality verified leads.

- **ConversionActionService** — Manage conversion actions to align Google Ads conversion tracking with EPI's verified lead data.

## Tool Mockups

### Onboarding — Google Ads Connection (Step 2 of 5)

```
+--------------------------------------------------+
|                                                  |
|   Step 2: Connect Google Ads                     |
|                                                  |
|   Link your Google Ads account to automatically  |
|   import campaign data and track ad spend.       |
|                                                  |
|                  [ O ]                            |
|             (Link icon)                          |
|                                                  |
|          [  Connect Google Ads  ]                |
|              (blue button)                       |
|                                                  |
|   ──────────────────────────────────────         |
|   Skip for now                                   |
|                                                  |
+--------------------------------------------------+
```

*After clicking "Connect Google Ads", the user is redirected to Google's OAuth consent screen, then back to our app with an authorization code.*

### Dashboard — Sites Overview

```
+------------------------------------------------------------------+
|  EPI Dashboard                           user@company.com [Logout]|
+------------------------------------------------------------------+
|                                                                    |
|  +--------------+  +----------------+  +--------------+           |
|  | Total Sites  |  | Verified Pixels|  | Total Leads  |           |
|  |      3       |  |      2         |  |     147      |           |
|  +--------------+  +----------------+  +--------------+           |
|                                                                    |
|  Sites                                          [ + Add Site ]    |
|  ─────────────────────────────────────────────────────────────    |
|  clientsite1.com       * Pixel  * Google  * Meta  * Slack  42 leads|
|  clientsite2.com       * Pixel  o Google  * Meta  o Slack  85 leads|
|  clientsite3.com       o Pixel  o Google  o Meta  o Slack   0 leads|
|                                                                    |
|  * = connected (green)    o = not connected (gray)                |
+------------------------------------------------------------------+
```

### Lead Monitor — Live Data View

```
+------------------------------------------------------------------+
|  * EPI Live Lead Monitor                    refreshes in 5s [Refresh]|
+------------------------------------------------------------------+
|                                                                    |
|  +----------+ +--------+ +----------+ +-----------+               |
|  |Total Leads| |Verified| |Suspicious| |   Junk    |               |
|  |   147     | |   98   | |    31    | |    18     |               |
|  +----------+ +--------+ +----------+ +-----------+               |
|  +--------+ +----------+ +----------+                             |
|  |Avg Score| |Attributed| |Duplicates|                             |
|  |  72/100 | |   112    | |    8     |                             |
|  +--------+ +----------+ +----------+                             |
|                                                                    |
|  Recent Leads                                                     |
|  ─────────────────────────────────────────────────────────────    |
|  Time     | Visitor  | Score | Quality    | Email | Attribution   |
|  ─────────────────────────────────────────────────────────────    |
|  2:34 PM  | a1b2c3d4 | 95/100| [verified] | valid | [definitive] |
|  2:31 PM  | e5f6a7b8 | 82/100| [verified] | valid | [high_conf]  |
|  2:28 PM  | c9d0e1f2 | 45/100| [suspicious]| catch-all| [probable]|
|  2:25 PM  | 34a5b6c7 | 12/100| [junk]     | invalid| [unattributed]|
|                                                                    |
+------------------------------------------------------------------+
```

### Platform Comparison Report (Google Ads vs EPI)

```
+------------------------------------------------------------------+
|  Attribution Comparison                                           |
|  Site: clientsite1.com    Platform: Google Ads    Date: 2026-03-01|
+------------------------------------------------------------------+
|                                                                    |
|  Google Ads Reported          |  EPI Verified                     |
|  ─────────────────────        |  ──────────────                   |
|  Conversions:    45           |  Total Leads:      38             |
|  Clicks:        320           |  Verified Leads:   29             |
|  Spend:     $412.50           |  Junk Leads:        5             |
|                               |                                   |
|  ─────────────────────────────────────────────────                |
|  Discrepancy:  35.6%  (Google over-reporting by 16 conversions)   |
|  Cost per Verified Lead:  $14.22                                  |
|                                                                    |
+------------------------------------------------------------------+
```

*This report shows that Google Ads reported 45 conversions for the day, but EPI's first-party verification confirmed only 29 as real, verified leads — a 35.6% discrepancy. The true cost-per-verified-lead is $14.22, not the $9.17 that Google's numbers would suggest.*

---

## Data Handling and Security

- **OAuth tokens** are encrypted at rest using Fernet symmetric encryption and never logged
- **No PII from Google Ads** is stored — we only pull aggregate campaign performance metrics
- **All data access** requires authentication (JWT or API key)
- **Tenant isolation** ensures each client organization can only see their own data (row-level security in PostgreSQL)
- **Google Ads data** for each client is used exclusively to generate that client's comparison reports and is never shared with other clients or externally
