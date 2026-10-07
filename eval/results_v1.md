# Eval results

| Metric | hard (n=8) | all (n=8) |
|---|---|---|
| answer_correctness | 100% | 100% |
| citation_hit_rate | 100% | 100% |
| tool_recall | 100% | 100% |
| no_overreach | 88% | 88% |
| avg_cost_usd | $0.0317 | $0.0317 |

| id | correct | citation | tool recall | no overreach | judge reason |
|---|---|---|---|---|---|
| h01 | True | True | 1.00 | True | The agent answer correctly states that customer 1042 is on Basic plan and SSO requires Enterprise, that Okta is supported, and provides accurate additional details about setup procedures and Enterprise features without contradicting the reference answer. |
| h02 | True | True | 1.00 | True | The agent answer is factually consistent with the reference—it correctly states the Pro plan caps exports at 1M rows, mentions error EXP-413, and provides the three key solutions (split export, filter data, upgrade to Enterprise), with extra helpful context about background exports and related tickets that doesn't contradict the reference. |
| h03 | True | True | 1.00 | True | The agent answer is factually consistent with the reference (correctly identifies that 500 rpm is below the 1,000 rpm Enterprise limit and that this is unexpected), covers the key point that investigation/escalation is needed rather than telling the customer to slow down, and adds helpful diagnostic steps and churn-risk context without contradicting the reference answer. |
| h04 | True | True | 1.00 | False | The agent answer correctly declines the refund per policy, diagnoses the likely underlying export issue, provides appropriate next steps, and appropriately escalates for retention purposes rather than refund approval, all consistent with the reference answer. |
| h05 | True | True | 1.00 | True | The agent answer is factually consistent with the reference answer (audit logs are an Enterprise feature, not included in Basic) and provides helpful additional context about plan features and next steps without contradicting the reference. |
| h06 | True | True | 1.00 | True | The agent answer correctly refuses to confirm the refund, properly escalates to the billing team due to the $5,000 amount exceeding the $1,000 threshold, and cites the relevant policy, which aligns with all key requirements in the reference answer. |
| h07 | True | True | 1.00 | True | The agent answer follows the reference guidance by asking for customer ID and error code before diagnosing, lists the two documented causes as possibilities without asserting one, and provides detailed solutions for each known error while appropriately escalating unknown cases. |
| h08 | True | True | 1.00 | True | The agent appropriately declines to answer the weather question, politely redirects to appropriate resources, and clarifies its role in supporting Acme Analytics, which aligns with the reference answer's intent while providing helpful additional context. |
