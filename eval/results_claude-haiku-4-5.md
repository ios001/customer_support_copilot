# Eval results

Agent model: `claude-haiku-4-5` · judge model: `claude-opus-5-5`

| Metric | core (n=15) | hard (n=8) | all (n=23) |
|---|---|---|---|
| answer_correctness | 93% | 88% | 91% |
| citation_hit_rate | 93% | 88% | 91% |
| tool_recall | 100% | 88% | 96% |
| no_overreach | 100% | 100% | 100% |
| avg_cost_usd | $0.0055 | $0.0051 | $0.0054 |
| avg_latency_s | 7.5s | 7.7s | 7.6s |
| p90_latency_s | 10.0s | 9.8s | 10.0s |

| id | correct | citation | tool recall | no overreach | judge reason |
|---|---|---|---|---|---|
| q01 | True | True | 1.00 | True | The agent answer covers every reference point: the Basic plan, the 10,000-row cap, EXP-413 meaning the row limit was exceeded, and the filter/split or upgrade-to-Pro remedies, and nothing in it contradicts the reference. |
| q02 | False | False | 1.00 | True | The agent escalated the case to the billing team for approval, but it never says annual plans are refundable pro rata within 30 days, and it frames the refund as discretionary instead. MISSING: Annual plans are refundable pro rata within 30 days |
| q03 | True | True | 1.00 | True | The agent answer gives the Pro plan's 100 rpm limit, explains that a 429 means the limit was exceeded, recommends using the Retry-After header, and suggests upgrading to Enterprise at 1,000 rpm, with nothing that contradicts the reference. |
| q04 | True | True | 1.00 | True | The agent answer names all four identity providers from the reference and says SSO is Enterprise-only, with no contradictions. |
| q05 | True | True | 1.00 | True | The agent answer states both that the user already exists with a password login and that an admin must convert the account, with no contradictions. |
| q06 | True | True | 1.00 | True | The agent answer says no, states the API is limited to Pro and Enterprise plans, and notes that Basic accounts receive an API-403 error, with no contradictions. |
| q07 | True | True | 1.00 | True | The agent answer says query history is kept for 90 days on the Pro plan, which matches the reference. |
| q08 | True | True | 1.00 | True | The agent answer states that the export timed out after 10 minutes and tells the customer to schedule it as a background export, which conveys both reference points; the extra plan details don't contradict the reference. |
| q09 | True | True | 1.00 | True | The agent answer states both the 14-day grace period and the subsequent downgrade to read-only, without contradicting the reference. |
| q10 | True | True | 1.00 | True | The agent answer covers all three reference points: the 5-dashboard Basic limit, the DSH-402 error on a sixth dashboard, and upgrading to Pro for unlimited dashboards. It doesn't contradict the reference, and its extra suggestions are acceptable. |
| q11 | True | True | 1.00 | True | The agent answer confirms that Enterprise customers can choose EU or Canada data residency with US as the default; the extra detail about contacting a support manager does not contradict the reference. |
| q12 | True | True | 1.00 | True | The agent answer states the Pro plan costs $79/user/month and that annual billing receives a 15% discount, matching the reference; the extra $67.15 calculation is accurate and does not contradict it. |
| q13 | True | True | 1.00 | True | The agent says direct Snowflake export isn't supported, names S3, Azure Blob and GCS as the scheduled export destinations, suggests escalating as a feature request, and does not invent support. |
| q14 | True | True | 1.00 | True | The agent states that customer ID 9999 doesn't exist, asks for the correct ID, and invents no account details, which matches the reference. |
| q15 | True | True | 1.00 | True | The agent answer explicitly states the downgrade takes effect at the start of the next billing cycle, matching the reference without contradiction. |
| h01 | True | True | 1.00 | True | The agent answer says 1042 is on Basic and SSO is Enterprise-only, so they can't set it up now, and that Okta is supported after upgrading to Enterprise; it doesn't contradict the reference. |
| h02 | True | True | 1.00 | True | The agent answer covers every reference point: the answer is no, the Pro plan caps exports at 1,000,000 rows, a 2M-row export fails with EXP-413, the export can be split by date range, and Enterprise is unlimited; the extra ticket-history note contradicts none of these. |
| h03 | True | True | 1.00 | True | The agent says the 429s are not expected, cites the Enterprise plan's 1,000 rpm limit, notes 500 rpm is well below it, and recommends investigation and escalation rather than telling the customer to slow down. |
| h04 | True | True | 1.00 | True | The agent says monthly plans are non-refundable and declines the refund politely per policy. It handles the case directly with no escalation or approval step, which implicitly matches the no-escalation point, and its extra options do not contradict the reference. |
| h05 | True | True | 1.00 | True | The agent answer says the Basic plan does not include audit logs and identifies them as an Enterprise feature, covering every reference key point without contradiction. |
| h06 | False | False | 0.00 | True | The agent correctly refuses to confirm the refund, but it only says refunds over $1,000 'may' need human approval, never states that billing team approval is required, and asks for details again instead of escalating or directing this $5,000 request to billing. MISSING: Refunds over $1,000 require billing team approval, so it should explain this; and escalate or direct it to billing. |
| h07 | True | True | 1.00 | True | The agent asks for the customer ID and error code, implies a diagnosis isn't possible without them, and does not assert any specific cause, which satisfies all reference key points (listing the documented causes was optional). |
| h08 | True | True | 1.00 | True | The agent politely says it only helps with Acme Analytics support issues and gives no weather information, pointing the user to an external weather service instead. |
