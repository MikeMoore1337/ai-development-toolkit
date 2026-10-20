# Stable Playwright UI checks

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A settings form saves a display name asynchronously and shows a confirmation.

## Procedure and decision

Use role-based locators, local fixtures and observable assertions. Assert saved data after reload; use Playwright trace-on-failure according to project config. Check accessibility and mobile viewport when relevant.

## Observable oracle

The saved value survives reload and a server error shows an actionable error without losing input. The assertion waits on UI state rather than arbitrary time.

## Failure or exclusion

Do not use waitForTimeout as the default synchronization or call intercepted mock responses proof of real backend persistence.

## Handoff contract

`test name | version | UI locator and oracle | backend boundary | trace or screenshot | observed result`

## Illustrative example

```ts
// Illustrative: execute only in a Playwright-enabled project.
await page.getByRole('textbox', { name: 'Display name' }).fill('Ada');
await page.getByRole('button', { name: 'Save' }).click();
await expect(page.getByRole('status')).toContainText('Saved');
await page.reload();
await expect(page.getByRole('textbox', { name: 'Display name' })).toHaveValue('Ada');
```
