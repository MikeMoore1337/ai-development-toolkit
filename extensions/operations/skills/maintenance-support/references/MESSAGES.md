# Customer replies (drafts only unless authorized)

| State | Evidence-aware text pattern |
| --- | --- |
| Intake | "We received your report. We are checking the conditions; a fix is not yet confirmed." |
| Need details | "Could you share the app version and last action before the problem? No logs needed for now." |
| Not reproduced | "The behavior did not occur in the tested environment. This does not rule out the reported issue." |
| Reproduced | "We reproduced the issue in [tested version/environment]. The cause and release date are not yet confirmed." |
| Known issue | "The symptom is confirmed in [scope]. [Verified workaround and its limitations, if any]." |
| Fix QA | "The change passed [specific tests]. Availability in your installation is not yet confirmed." |
| Published | "The fix is included in [published version]. Publication does not mean every device has updated." |
| Deployed | "The fix reached [verified channel/environment], but we have not checked your installed build." |
| Rolled back | "The update was rolled back in [scope]. The previous problem may recur." |
| Deprecated | "The feature is changing under [approved policy]. Follow [tested migration steps]." |
| User verified | "Your confirmation on [matching version/environment] shows the scenario works; the report can be closed as verified." |

Preserve message ID, related report, audience, verified facts/unknowns, required approval and DRAFT/READY_FOR_REVIEW/APPROVED/SENT/DELIVERY_CONFIRMED/NOT_SENT/BLOCKED state. Even approved is not sent. Scrub emails, tokens, cookies, secrets, private URLs, personal identifiers and private logs. Do not promise dates, security guarantees, data integrity or an SLA without evidence. Vulnerabilities use responsible private disclosure rather than public exploit details.
