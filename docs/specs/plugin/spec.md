# Plugin

## Purpose

## Requirements

### REQ-PLUGIN-001: Installable plugin with two skills
The repository SHALL be a Claude Code plugin whose manifest exposes exactly two skills, `sa-design` and `sa-review`, installable into any project from a local path or marketplace entry.

#### Scenario: Install into a new project
- GIVEN a project without the plugin
- WHEN the user installs the plugin from this repository
- THEN `/sa-design` and `/sa-review` are available in that project's Claude Code session
