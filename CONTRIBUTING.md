# Contributing Guidelines

Thank you for your interest in contributing to FactGuard (Cek Fakta).

## Development Workflow

1. Fork the repository and clone your fork locally.
2. Install dependencies:
   - Backend: `pip install -r requirements.txt`
   - Frontend: `npm install`
3. Run tests before submitting changes:
   ```bash
   pytest api/tests/ -v
   npm run lint
   ```
4. Adhere to Conventional Commits and ensure zero credential leaks.
5. Open a Pull Request targeting `main`.
