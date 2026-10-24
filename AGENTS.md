# Repository workflow

- Use `dev` for Windows development and `linux_dev` for Linux/Steam Proton development.
- Treat `master` and `linux_master` as stable release snapshot branches. Each must contain only its platform's release commits.
- Never merge, fast-forward, or rebase a development branch into a release branch, because that copies development history into the release branch.
- Update either release branch, move release tags, or publish a GitHub Release only after the user gives an explicit one-time instruction for that exact platform and version.
- For a release, create one new commit on top of the matching release branch whose tree matches the approved development snapshot. Tag that commit and attach the built platform artifact to the matching GitHub Release.
- Keep `linux_master` empty until the user explicitly authorizes the first Linux release.
- After releasing, switch the working checkout back to the matching development branch. A completed release does not grant permission for later release-branch updates.
