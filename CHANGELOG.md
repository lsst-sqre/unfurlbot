# Change log

unfurlbot is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/unfurlbot/tree/main/changelog.d/).

<!-- scriv-insert-here -->

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
