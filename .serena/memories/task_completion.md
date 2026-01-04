# HN Herald - Task Completion Checklist

## Before Marking Task Complete

### Quality Gates (Required)
1. **Tests Pass**
   ```bash
   make test
   # OR
   uv run pytest
   ```

2. **Linting Passes**
   ```bash
   make lint
   # OR
   uv run ruff check src/ tests/
   ```

3. **Type Checking Passes**
   ```bash
   make typecheck
   # OR
   uv run mypy src/
   ```

4. **Code Formatted**
   ```bash
   make format
   # OR
   uv run ruff format src/ tests/
   ```

### Coverage Requirements
- Minimum coverage: 70%
- Run coverage check:
  ```bash
  make test-cov
  ```

### Documentation Updates
- [ ] Update tasks.md with task status
- [ ] Update relevant docs if behavior changed
- [ ] Add docstrings to new public functions

### Git Workflow
1. Commit frequently (every 15-30 minutes)
2. Use conventional commit messages:
   - `feat:` New feature
   - `fix:` Bug fix
   - `refactor:` Code change (no behavior)
   - `test:` Adding tests
   - `docs:` Documentation
   - `chore:` Maintenance

### Pre-commit Verification
```bash
# Run all pre-commit hooks
pre-commit run --all-files
```

## Quick Validation Command
```bash
# Run all quality gates at once
make all
```
This runs: install → lint → typecheck → test

## Session End Checklist
1. Run `make test && make lint`
2. Update tasks.md with session log
3. Commit all changes
4. Push to feature branch
