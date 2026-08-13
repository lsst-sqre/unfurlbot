---
name: dependabot-build-manifest-gate
description: Cross-repo CI bug — multiplatform-build-and-push@v4 build job gated to tickets/** blocks dependabot PRs on the required build/manifest check
metadata:
  type: reference
---

Any lsst-sqre repo whose `main` ruleset requires the `build / manifest`
status check AND whose `ci.yaml` `build` job (the reusable
`lsst-sqre/multiplatform-build-and-push/.github/workflows/build.yaml@v4`)
only runs for releases + `tickets/**` will silently **block every
`dependabot/**` PR**: the reusable workflow never instantiates, so
`build / manifest` is never reported and the strict ruleset (no merge
queue) leaves the PR un-mergeable.

Fix (verbatim port): extend the build job's `if:` to also match
`startsWith(github.head_ref, 'dependabot/')`, and pass `push:` as an
expression true only for releases + `tickets/**`. Dependabot then builds
the Dockerfile on both arches (real coverage for base-image bumps) while
the push-gated `manifest` job is skipped — which the ruleset treats as
passing. No registry secrets needed.

Reference implementations: lsst-sqre/squarebot#48 (PRD #36, DM-51754),
lsst-sqre/unfurlbot#31 (PRD #23, DM-51754). When doing
maintenance-rounds / catch-up-discovery across the other SQuaRE apps,
check each repo for this same gap.
