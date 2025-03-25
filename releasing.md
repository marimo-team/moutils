# Release Process

This document outlines the process for creating a new release of moutils.

## Creating a Release

1. Update version in `pyproject.toml`
2. Commit changes:

   ```sh
   git add pyproject.toml
   git commit -m "Bump version to x.y.z"
   ```

3. Tag the release:

   ```sh
   git tag -a x.y.z -m "Release version x.y.z"
   ```

4. Push changes:

   ```sh
   git push origin main && git push origin x.y.z
   ```

5. GitHub Actions will automatically build and publish the package to PyPI when the tag is pushed.

```sh

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes
