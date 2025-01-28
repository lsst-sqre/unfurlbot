# Change log

unfurlbot is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/unfurlbot/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-0.5.0'></a>

## 0.5.0 (2025-01-28)

### New features

- Unfurlbot now ignores trigger messages if they are older than `UNFURLBOT_SLACK_TRIGGER_MESSAGE_TTL` (a time in seconds). This prevents unfurling messages that are no longer relevant and mitigates circumstances where Unfurlbot may be processing old messages.

### Other changes

- Refactored the `DomainUnfurler` base class so that the `process_slack` method now calls two hooks that subclasses need to implement: `extract_tokens` and `create_slack_message`. With this structure the pipeline for processing Slack messages is more consistent and easier to implement for new unfurling domains.

- Improved logging. All log messages for a given token include context about the token, token type (e.g. `jira`), the channel ID, and the timestamps of the triggering message and thread (if applicable). Log messages are sent for `Sent unfurl` events, and warnings are logged for `Ignoring stale trigger message` events.

<a id='changelog-0.4.0'></a>

## 0.4.0 (2024-12-05)

### New features

- Allow configuration of the timeout when making requests to the Jira server instead of only using the 20s default.

<a id='changelog-0.3.2'></a>

## 0.3.2 (2024-12-02)

### Bug fixes

- Require Jira ticket references start at a word boundary so that, for example, `LDM-1234` is not detected as ticket `DM-1234`.

<a id='changelog-0.3.1'></a>

## 0.3.1 (2024-10-10)

### Bug fixes

- Fix processing of bot messages by updating to the latest Kafka models.

<a id='changelog-0.3.0'></a>

## 0.3.0 (2024-07-25)

### New features

- Unfurlbot now processes messages from other bots.

<a id='changelog-0.2.2'></a>

## 0.2.2 (2024-07-22)

### Bug fixes

- Make `description` optional in the JiraIssueSummmary model. Rubin epics typically do not have descriptions in the same manner as regular issues. Since we don't use the description field in the unfurl, we can safely make it optional.
- Normalize dates in the JiraIssueSummary so that they are consistently converted to the UTC timezone.
- Updated `ProcessContext` to call `aclose` rather than `close` on the Redis client.

### Other changes

- Unfurlbot is now formatted with Ruff.
- Adopt uv and tox-uv for package installation and dependency resolution.

<a id='changelog-0.2.1'></a>

## 0.2.1 (2024-04-03)

### Bug fixes

- Stop using the mrkdwn quote in the main unfurled content because it down't present well in mobile views.

<a id='changelog-0.2.0'></a>

## 0.2.0 (2024-03-04)

### New features

- Unfurlbot now uses Redis to store unfurl events and debounce unfurls to the same channel or thread. By default, Unfurlbot won't unfurl the same Jira issue to the same channel or thread more than once every 5 minutes. This can be configured with the `UNFURLBOT_SLACK_DEBOUNCE_TIME` environment variable.

<a id='changelog-0.1.0'></a>

## 0.1.0 (2024-02-29)

### New features

- This is the first release of Unfurlbot. Unfurlbot listens to messages from [Squarebot](https://github.com/lsst-sqre/squarebot) over Kafka and unfurls information about identifiers back to the conversation. At release, Unfurlbot supports unfurling Jira issue keys mentioned in Slack. Unfurlbot works with the [Jira Data Proxy](https://github.com/lsst-sqre/jira-data-proxy) to fetch Jira issue information. On release, Unfurlbot is missing the following features:

  - Unfurls are not debounced, so Unfurlbot will respond with the same unfurl message in a conversation if its mentioned several times.

  - Attachments are not scanned for content.
