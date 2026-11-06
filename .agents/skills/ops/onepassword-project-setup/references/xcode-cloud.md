# Xcode Cloud and the 1Password model

Xcode Cloud keeps its own secret environment variables per workflow. It does
not read 1Password or run `op run`. Keep each variable as a recorded projection
of its owning 1Password item, whether project-specific or shared. Record every
deployed copy in the item's notes and coordinate their replacement on rotation.

Before adding a key, read the project's shared release contract, operation
profiles and existing identity register. Reuse the reviewed profile and custody;
this setup step does not require a new per-project App Store Connect key.

- Read/build admission and Apple permissions are different boundaries. A
  workflow can archive and distribute through its [post-actions][workflow].
  Development-role or Dev-vault labels are not proof of read-only access;
  review the workflow and [role permissions][roles] together.
- Publishing/submission authority stays in its reviewed release custody and
  approved consumers. Do not copy a shared release key into a Dev/CI item or
  broaden a consumer's grant to simplify setup.
- A GitHub callback App is a different job from Apple operations or tag
  creation. Reuse the existing job-specific App only within its accepted
  repository/workflow trust boundary; callback access is not tag-write access.

An existing project-specific pilot may keep its reviewed key and projections;
reconcile its recorded scope before changing it. New credentials, migrations,
permissions, workflow secret copies and release operations require their own
applicable authorization. Load approved references only in the provider step
through the shared loader or the standalone template, as the project contract
requires. Never print key material or infer release authority from a read check.

[workflow]: https://developer.apple.com/documentation/xcode/xcode-cloud-workflow-reference
[roles]: https://developer.apple.com/help/app-store-connect/reference/account-management/role-permissions
