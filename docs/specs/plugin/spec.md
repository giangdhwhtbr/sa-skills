# Plugin

## Purpose

## Requirements

### REQ-PLUGIN-001: Installable plugin with four skills
The repository SHALL be a Claude Code plugin whose manifest exposes exactly four skills, `sa-design`, `sa-review`, `sa-diagrams` and `sa-deck`, installable into any project from a local path or marketplace entry.

#### Scenario: Install into a new project
- GIVEN a project without the plugin
- WHEN the user installs the plugin from this repository
- THEN `/sa-design`, `/sa-review`, `/sa-diagrams` and `/sa-deck` are available in that project's Claude Code session
