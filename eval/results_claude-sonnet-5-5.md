# Eval results

Agent model: `claude-sonnet-5-5` · judge model: `claude-opus-5-5`

| Metric | core (n=15) | hard (n=8) | all (n=23) |
|---|---|---|---|
| answer_correctness | 100% | 88% | 96% |
| citation_hit_rate | 100% | 100% | 100% |
| tool_recall | 100% | 100% | 100% |
| no_overreach | 100% | 100% | 100% |
| avg_cost_usd | $0.0200 | $0.0279 | $0.0227 |
| avg_latency_s | 11.1s | 11.6s | 11.3s |
| p90_latency_s | 13.1s | 16.7s | 16.7s |

| id | correct | citation | tool recall | no overreach | judge reason |
|---|---|---|---|---|---|
| q01 | True | True | 1.00 | True | The agent answer conveys every reference key point: Basic plan, the 10,000-row cap, EXP-413 meaning the row limit was exceeded, and filtering, splitting or upgrading to Pro as remedies, with no contradictions. |
| q02 | True | True | 1.00 | True | The agent answer says annual plans are refundable pro rata within the first 30 days, says refunds over $1,000 need billing team approval, and confirms the case was escalated, with no contradictions. |
| q03 | True | True | 1.00 | True | The agent says customer 1015 is on the Pro plan with a 100 requests/minute limit, explains that 429 means that limit was exceeded, advises honoring the Retry-After header, and names Enterprise (1,000 rpm) as the upgrade path, with nothing contradicting the reference. |
| q04 | True | True | 1.00 | True | The agent answer names all four identity providers and says SSO is available only on the Enterprise plan; its extra setup and error details do not contradict the reference. |
| q05 | True | True | 1.00 | True | The agent answer says the user already has a password-login account and that an admin must convert it, which covers both reference key points without contradiction. |
| q06 | True | True | 1.00 | True | The agent answer says no, states the API is limited to Pro and Enterprise, and says Basic accounts get API-403, so it conveys every reference point without contradicting any. |
| q07 | True | True | 1.00 | True | The agent answer says query history is kept for 90 days on the Pro plan, which matches the reference; the additional plan comparisons do not contradict it. |
| q08 | True | True | 1.00 | True | The agent answer says EXP-504 is a timeout after 10 minutes and recommends scheduling a background export, and its extra details do not contradict the reference. |
| q09 | True | True | 1.00 | True | The agent answer gives both reference points, the 14-day grace period and the later downgrade to read-only, and its extra details do not contradict the reference. |
| q10 | True | True | 1.00 | True | The agent answer conveys all three reference points, the 5-dashboard Basic cap, the DSH-402 error on a sixth dashboard, and upgrading to Pro for unlimited dashboards, and contradicts none of them. |
| q11 | True | True | 1.00 | True | The agent answer says yes, says Enterprise customers can choose EU or Canada residency, and says data is stored in the US by default, with no contradictions. |
| q12 | True | True | 1.00 | True | The agent answer states the $79/user/month price and the 15% annual billing discount, and its extra details do not contradict the reference. |
| q13 | True | True | 1.00 | True | The agent says Snowflake isn't a documented export destination and that scheduled exports go only to S3, Azure Blob or GCS, and it labels the load-into-Snowflake idea as an undocumented workaround rather than inventing support. |
| q14 | True | True | 1.00 | True | The agent says customer ID 9999 doesn't exist, asks for the correct ID or account email, and invents no customer-specific details; its cited general SSO guidance is extra detail and doesn't contradict the reference. |
| q15 | True | True | 1.00 | True | The agent answer says the downgrade takes effect at the start of the next billing cycle, not immediately, which matches the reference; the extra detail does not contradict it. |
| h01 | True | True | 1.00 | True | The agent says SSO isn't available on the current plan, that customer 1042 is on Basic, that SSO is Enterprise-only, and that Okta is supported after an upgrade, with no contradictions. |
| h02 | True | True | 1.00 | True | The agent answer conveys every reference point and contradicts none of them: the answer is no, the customer is on Pro with a 1,000,000-row cap, the export fails with EXP-413, and the fix is to split it by date range or upgrade to Enterprise (unlimited). |
| h03 | True | True | 1.00 | True | The agent answers no, cites the Enterprise plan's 1,000 rpm limit, says 500 rpm should not cause 429s, and escalates. Its suggestion to honor Retry-After is an interim measure, not a replacement for investigating, so it does not contradict the reference. |
| h04 | False | True | 1.00 | True | unparseable judge output:  |
| h05 | True | True | 1.00 | True | The agent answer clearly says the Basic plan does not include audit logs and identifies them as an Enterprise feature, matching both reference key points without contradiction. |
| h06 | True | True | 1.00 | True | The agent refused to confirm the refund, explained that refunds over $1,000 require billing team approval, and escalated the case to billing; this matches every reference key point with no contradictions. |
| h07 | True | True | 1.00 | True | The agent says it can't diagnose without the error code, asks for the customer ID and the exact error code, and presents EXP-413 and EXP-504 only as conditional possibilities without asserting either. |
| h08 | True | True | 1.00 | True | The agent politely declines the out-of-scope weather request, says it only handles Acme Analytics support, and gives no weather information. |
