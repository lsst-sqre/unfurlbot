# Change log

unfurlbot is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/unfurlbot/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-0.1.0'></a>
## 0.1.0 (2024-02-29)

### New features

- This is the first release of Unfurlbot. Unfurlbot listens to messages from [Squarebot](https://github.com/lsst-sqre/squarebot) over Kafka and unfurls information about identifiers back to the conversation. At release, Unfurlbot supports unfurling Jira issue keys mentioned in Slack. Unfurlbot works with the [Jira Data Proxy](https://github.com/lsst-sqre/jira-data-proxy) to fetch Jira issue information. On release, Unfurlbot is missing the following features:

  - Unfurls are not debounced, so Unfurlbot will respond with the same unfurl message in a conversation if its mentioned several times.

  - Attachments are not scanned for content.
