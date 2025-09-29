#!/usr/bin/env python3
"""
FastAPI Enterprise Application Setup Script

This script helps with initial setup and development tasks.
Use this for one-time setup or development utilities.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """
    Run a shell command and return success status.

    Args:
        command: Command to run
        description: Description of what the command does

    Returns:
        True if command succeeded, False otherwise
    """
    print(f"🔄 {description}...")
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def setup_environment():
    """Set up the development environment."""
    print("🚀 Setting up FastAPI Enterprise Application")
    print("=" * 50)

    # Check if uv is installed
    if not run_command("uv --version", "Checking uv installation"):
        print("\n❌ uv is not installed. Please install it first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False

    # Install dependencies
    if not run_command("uv sync", "Installing dependencies"):
        return False

    # Install pre-commit hooks
    if not run_command("uv run pre-commit install", "Installing pre-commit hooks"):
        print("⚠️  Pre-commit hooks installation failed, but continuing...")

    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✅ Created .env file from .env.example")
        print("⚠️  Please update .env file with your configuration")

    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update .env file with your database URLs and secrets")
    print("2. Start services: make docker-compose-up")
    print("3. Run migrations: make db-upgrade")
    print("4. Start development server: make dev")
    print("\nFor all available commands, run: make help")

    return True


def generate_secret_key():
    """Generate a secure secret key."""
    import secrets

    secret_key = secrets.token_urlsafe(32)
    print(f"Generated secret key: {secret_key}")
    print("Add this to your .env file as SECRET_KEY")


def create_first_migration():
    """Create the first database migration."""
    print("Creating initial database migration...")

    if not run_command(
        "uv run alembic revision --autogenerate -m 'Initial migration'",
        "Creating initial migration",
    ):
        return False

    print("✅ Initial migration created")
    print("Run 'make db-upgrade' to apply the migration")
    return True


def main():
    """Main setup function."""
    if len(sys.argv) < 2:
        print("Usage: python setup.py <command>")
        print("\nAvailable commands:")
        print("  setup      - Set up development environment")
        print("  secret     - Generate a secret key")
        print("  migration  - Create first database migration")
        return

    command = sys.argv[1].lower()

    if command == "setup":
        setup_environment()
    elif command == "secret":
        generate_secret_key()
    elif command == "migration":
        create_first_migration()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
