# Contributing to Daily Forge

Thank you for your interest in contributing! Daily Forge is an open-source project focused on helping people build consistent posting habits.

## Getting started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally.
3. **Set up** the dev environment:

```bash
cd daily-forge
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn daily_forge.main:app --reload
```

4. **Create a branch** for your work:

```bash
git checkout -b feature/your-feature-name
```

## How to contribute

### Bug reports

Open an issue with:

- Steps to reproduce
- Expected vs actual behavior
- OS and Python version
- Screenshots if UI-related

### Feature requests

Check [ROADMAP.md](ROADMAP.md) first. Open an issue describing the problem you're solving, not just the solution.

### Pull requests

1. Keep PRs focused — one feature or fix per PR.
2. Match existing code style (type hints, docstrings on public functions).
3. Update docs if you change behavior (`README.md`, `SPEC.md`, or `AGENTS.md`).
4. Test manually: run the app, verify streak/heatmap/composer still work.

### Code style

- Python: PEP 8, type hints on function signatures
- JavaScript: vanilla ES6+, no frameworks unless discussed first
- CSS: use existing CSS variables in `static/style.css`
- Comments: explain *why*, not *what*

## Project areas

| Area | Files |
|------|-------|
| API / backend | `daily_forge/*.py` |
| UI template | `templates/index.html` |
| Client logic | `static/app.js` |
| Styling | `static/style.css` |
| Docs | `*.md` at root |

## Commit messages

Use clear, imperative subjects:

```
Add timezone setting to streak calculation
Fix heatmap alignment for Monday-start weeks
Update README with Pi deployment steps
```

## Community standards

- Be respectful and constructive in issues and reviews.
- Welcome newcomers — this project is for habit builders of all skill levels.
- No scope creep: resist adding social APIs or auth without discussion.

## Questions?

Open a GitHub Discussion or issue. For agent-assisted development, see [AGENTS.md](AGENTS.md).

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).