# Contributing to TrackFlow

Thank you for your interest in contributing to TrackFlow! We value all contributions, whether they're bug reports, feature requests, or code contributions.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up your development environment
4. Create a feature branch
5. Make your changes
6. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/trackflow.git
cd trackflow

# Create a new branch
git checkout -b feature/your-feature-name

# Install in development mode
bench get-app . --skip-assets
bench --site your-site.local install-app trackflow
bench --site your-site.local set-config developer_mode 1
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused
- Write self-documenting code

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting PR
- Test on both desktop and mobile views
- Check for console errors

```bash
bench --site your-site.local run-tests --app trackflow
```

## Commit Messages

Follow conventional commit format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

Example: `feat: add bulk link creation feature`

## Pull Request Process

1. Update documentation if needed
2. Add/update tests
3. Ensure CI passes
4. Request review from maintainers
5. Address feedback promptly

## Code Review

All submissions require review. We aim to provide feedback within 48 hours.

## Community

- Be respectful and inclusive
- Help others in discussions
- Share knowledge and learn together

## Questions?

Feel free to open an issue or reach out on our [discussion forum](https://github.com/chinmaybhatk/trackflow/discussions).

Thank you for making TrackFlow better! 🚀