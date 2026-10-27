# Repository workflow

- Do all development work on `dev`. Commit and push ordinary changes only to `dev`.
- Treat `master` as the stable release snapshot branch. It must contain one commit per published version.
- Never merge, fast-forward, or rebase `dev` into `master`, because that copies development history into the release branch.
- Update `master`, move release tags, or publish a GitHub Release only after the user gives an explicit one-time instruction for that exact release.
- For a release, create one new commit on top of the current `master` whose tree matches the approved `dev` snapshot. Tag that commit and attach the built Windows EXE to the matching GitHub Release.
- After releasing, switch the working checkout back to `dev`. A completed release does not grant permission for later `master` updates or releases.
