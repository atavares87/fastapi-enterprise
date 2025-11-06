# Cursor Rules - Layered Architecture

This directory contains organized development rules for the FastAPI Enterprise application using Cursor IDE's new rules format.

## 📚 Rules Organization

Rules are split into focused, topic-specific files for better organization and maintenance:

### Core Rules

1. **[00-overview.md](00-overview.md)** - Project overview and stack
   - Quick introduction to the project
   - Technology stack
   - Critical principles (standard practices first!)

2. **[01-architecture.md](01-architecture.md)** - Architecture overview
   - Layered architecture explanation
   - Directory structure
   - Dependency flow
   - SOLID principles

### Layer-Specific Rules

3. **[02-controller-layer.md](02-controller-layer.md)** - Controller layer (@RestController)
   - HTTP request/response handling
   - Thin controllers pattern
   - Anti-patterns to avoid

4. **[03-service-layer.md](03-service-layer.md)** - Service layer (@Service)
   - Business logic orchestration
   - Service method patterns
   - Coordination between repositories

5. **[04-repository-layer.md](04-repository-layer.md)** - Repository layer (@Repository)
   - Data access abstraction
   - Query and mutation patterns
   - Database interaction

6. **[05-domain-layer.md](05-domain-layer.md)** - Domain layer (Models & Core)
   - Domain models (entities, value objects)
   - Functional core (pure functions)
   - Immutability and purity

### Development Practices

7. **[06-testing.md](06-testing.md)** - Testing strategy
   - Test pyramid
   - Domain tests (no mocks!)
   - Service tests (mock repositories)
   - Integration tests

8. **[07-dependency-injection.md](07-dependency-injection.md)** - Dependency injection
   - Singleton pattern with `lru_cache`
   - Dependency graph
   - Spring-style DI

9. **[08-code-standards.md](08-code-standards.md)** - Code quality standards
   - Python standards
   - Type hints
   - Naming conventions
   - Documentation

10. **[09-development-workflow.md](09-development-workflow.md)** - Development workflow
    - Common commands
    - Adding new features
    - Git workflow
    - PR checklist

11. **[10-anti-patterns.md](10-anti-patterns.md)** - Common anti-patterns to avoid
    - General anti-patterns
    - Layer-specific anti-patterns
    - Functional core anti-patterns

### 🤖 AI Assistant Rules (CRITICAL)

12. **[11-ai-assistant-workflow.md](11-ai-assistant-workflow.md)** - ⚠️ **MANDATORY AI WORKFLOW**
    - **ALWAYS validate changes with tests and checks**
    - Run `make test` after code changes
    - Run `make check-all` after code changes
    - Fix all errors/warnings before completion
    - Never leave broken code

## 🎯 Quick Navigation

### By Role/Focus

**Frontend/API Developer?** Start with:
- `02-controller-layer.md` - HTTP endpoints
- `06-testing.md` - Testing controllers

**Backend Developer?** Start with:
- `03-service-layer.md` - Business logic
- `04-repository-layer.md` - Data access

**Domain Expert/Architect?** Start with:
- `01-architecture.md` - Overall structure
- `05-domain-layer.md` - Pure business logic

**New to Project?** Read in order:
1. `00-overview.md` - What is this?
2. `01-architecture.md` - How is it organized?
3. Your relevant layer file

**AI Assistant?** **MUST READ**:
- `11-ai-assistant-workflow.md` - **Validation workflow (MANDATORY)**

### By Task

**Adding a new feature?**
→ `09-development-workflow.md` - Step-by-step guide

**Writing tests?**
→ `06-testing.md` - Testing strategy

**Having code review issues?**
→ `10-anti-patterns.md` - What to avoid

**Setting up DI?**
→ `07-dependency-injection.md` - Dependency injection

**Helping with code (AI)?**
→ `11-ai-assistant-workflow.md` - **MUST FOLLOW**

## 🔍 How Cursor Uses These Rules

Cursor IDE automatically loads all `.md` files from this directory and uses them as context when:
- Generating code
- Suggesting refactorings
- Answering questions
- Code reviews

The numbered prefixes ensure rules are loaded in a logical order.

## 🤖 Special Note for AI Assistants

**Rule #11 (`11-ai-assistant-workflow.md`) is MANDATORY** when helping with code changes:

### ⚠️ CRITICAL: Always Validate Changes

After making ANY code changes, you MUST:

1. Run `make check-all` (code quality checks)
2. Run `make test` (all tests)
3. Fix any failures/errors/warnings
4. Re-run until everything passes
5. Only then consider task complete

**NEVER** finish a task with:
- ❌ Failing tests
- ❌ Linter errors
- ❌ Type check errors
- ❌ Unvalidated code

See `11-ai-assistant-workflow.md` for complete workflow details.

## 📝 Updating Rules

When updating rules:
1. Keep each file focused on one topic
2. Use examples liberally
3. Show both good and bad patterns
4. Keep it concise (< 500 lines per file)
5. Update this README if adding new files

## 🔄 Migration Note

These rules replace the old `.cursorrules` file. The new format offers:
- ✅ Better organization
- ✅ Easier navigation
- ✅ Focused, topic-specific rules
- ✅ Better maintainability
- ✅ Mandatory validation workflow (Rule #11)

The old `.cursorrules` file is kept for backward compatibility but may be removed in the future.

## 📚 Additional Documentation

For more detailed documentation, see:
- [Complete Architecture Guide](../../docs/architecture/layered-architecture.md)
- [Development Guide](../../docs/development/README.md)
- [Migration Summary](../../LAYERED_ARCHITECTURE_MIGRATION_SUMMARY.md)

## 🎓 Learning Path

### For Developers

1. Read `00-overview.md` (project intro)
2. Read `01-architecture.md` (architecture)
3. Read your layer-specific rules (02-05)
4. Read `09-development-workflow.md` (how to work)
5. Reference `10-anti-patterns.md` (what to avoid)

### For AI Assistants

1. **MUST READ**: `11-ai-assistant-workflow.md` ⚠️
2. Read `01-architecture.md` (understand structure)
3. Read layer rules (02-05) for code generation
4. Reference `06-testing.md` (testing requirements)
5. Reference `10-anti-patterns.md` (what to avoid)

---

**Remember**:
- **Developers**: Standard practices first! Follow documented patterns.
- **AI Assistants**: Always validate changes! Run tests and checks before completion.
