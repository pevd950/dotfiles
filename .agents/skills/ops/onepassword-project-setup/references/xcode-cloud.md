# Xcode Cloud and the 1Password model

Xcode Cloud keeps its own secret environment variables, configured per workflow in App Store Connect; they are not read from 1Password and `op run` does not exist inside an Xcode Cloud build. Treat each secret variable there as a copy of an item in the project's vault, recorded by name in the item's notes (where it is deployed), and rotate both together.

What the project's vaults hold for Xcode Cloud:

- `<Project> Dev`: an App Store Connect API key with the **Developer** role, item `App Store Connect <Project>-ci` (tags `project:<slug>`, `env:ci`, `consumer:ci`). Its only use is to trigger builds through the API (`POST /v1/ciBuildRuns`, after resolving the workflow and git reference IDs) from GitHub Actions or a local script; a Developer key cannot submit or release.
- `<Project> Prod`: nothing Xcode Cloud specific. The shared release key (Admin or App Manager role, used by `fastlane deliver`, TestFlight distribution, and release workflows) stays the team-level item in the Prod tier and is readable only by `sa-<project>-release`. Never copy it into the Dev vault or into a `ci`-consumer item: a leaked Dev-tier credential must not be able to ship a build.

To trigger a build from CI, load the Developer key with the `templates/load-secrets-step.yml` step (`op://<Project> Dev/App Store Connect <Project>-ci/key id`, `.../issuer id`, `.../private key`), mint the JWT in the step that calls the API, and map the outputs only into that step.
