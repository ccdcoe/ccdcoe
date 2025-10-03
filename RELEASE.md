# Release instructions

## Releasing new version of this package

After making all the necessary changes in the source code; change (and commit) the version number to the desired 
version in the `pyproject.toml` file; create a tag which corresponds to the version in the `pyproject.toml` file: 
`git tag -a v0.0.5 -m "Release version 0.0.5"` and push (both the commits and the tags) to the repo: 
`git push --follow-tags`.

**IMPORTANT NOTICE** the version in the `pyproject.toml` is set without the 'v' prefix like; `0.0.5` but in the tagging 
the version is prefixed by the `v`; if you do not prefix the version number in the tag, the workflow will ignore the 
tag and will not push the source code to pypi!
