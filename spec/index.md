# Spec Index

Canonical specs in this repository describe durable Exo/personal-agent product
behavior and deployment contracts. Linear issues hold workflow state; this
directory holds the durable source of truth that implementers, reviewers, and
operators should read when changing the agent distribution.

## Domains

- [Hermes Personal Agent Distribution](./domains/hermes-personal-agent-distribution.md):
  shared Hermes profile-distribution, optional profile variants, multi-repo
  skill installation, one-container-per-agent deployment, remote SSH
  redeployability, TOML config validation, Phase-backed secret materialization,
  storage-zone contracts, and v1 Telegram/runtime boundaries for Tom, Alex
  Example, and Sam Example personal agents.
- [Project Conventions](./domains/project-conventions.md): repo-local path,
  config, secrets, and fake-smoke conventions for distribution-owned material.
- [Repository Regression Suite](./domains/repository-regression-suite.md):
  validation commands and expected local smoke coverage for this repository.
