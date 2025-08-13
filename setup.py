"""Setup script for Datadog MCP Client."""
import os
import shutil
from pathlib import Path


def setup_environment():
    """Set up the development environment."""
    print("🔧 Setting up Datadog MCP Client environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
        print("⚠️  Please edit .env file with your Datadog OAuth credentials")
    
    print("\n📋 Next steps:")
    print("1. Edit .env file with your Datadog OAuth app credentials")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the client: python main.py")
    print("\n🔗 To create a Datadog OAuth app:")
    print("   Visit: https://app.datadoghq.com/account/settings#api")
    print("   Click 'OAuth Apps' and create a new application")
    print("   Set redirect URI to: http://localhost:8080/callback")


if __name__ == "__main__":
    setup_environment()
