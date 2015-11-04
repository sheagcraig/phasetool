# phasetool
This is a work-in-progress project to automate phase testing of software with Munki.

For the immediate future, it will automate _my_ _environement_; but the longterm goal is to make use of flexible configurations to allow it to be customized to meet a variety of organization's needs.

## Features (Existing)
- Bulk disable the `unattended_install key` (if present)
- Bulk set a `force_install_after_date`

## Features (Planned and In-Progress)
- Generate markdown file listing the updates to be phase tested.
	- Includes basic metadata about update: version, description, name, display name.
	- We manage our phase testing comments with Gitlab issues. The markdown will include flexibly configured links to your preferred support site.
- Automate the notification of clients (via Slack and email), of the phase testing schedule.
- Automate the rollover of packages from one catalog to the next.
	- Currently, at my organization, we allow the phase testing groups to optionally update during a given window of time, after which they become forced.
	- Upon promotion to production, updates become unattended.
- Reporting of current installation distribution, issues raised, and schedule.
- I would like to transition from monthly phase testing tied to the Microsoft "Patch-Tuesday" schedule to a rolling phase testing schedule. So eventually, this tool will support that.