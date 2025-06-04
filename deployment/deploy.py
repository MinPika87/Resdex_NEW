"""
Deployment script for ResDex Agent.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
import yaml


def load_config(environment: str) -> dict:
    """Load deployment configuration for environment."""
    config_file = Path(__file__).parent / "config" / f"{environment}.yaml"
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def deploy_streamlit(config: dict):
    """Deploy Streamlit application."""
    print("🚀 Deploying Streamlit application...")
    
    # Set environment variables
    for key, value in config.get('environment', {}).items():
        os.environ[key] = str(value)
    
    # Install dependencies
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
    
    # Run Streamlit
    cmd = [
        "streamlit", "run", 
        "resdx_agent/ui/streamlit_app.py",
        "--server.port", str(config.get('port', 8501)),
        "--server.address", config.get('host', '0.0.0.0')
    ]
    
    subprocess.run(cmd)


def deploy_docker(config: dict):
    """Deploy using Docker."""
    print("🐳 Deploying with Docker...")
    
    # Build Docker image
    subprocess.run(["docker", "build", "-t", "resdx-agent", "."], check=True)
    
    # Run container
    cmd = [
        "docker", "run", "-d",
        "--name", "resdx-agent",
        "-p", f"{config.get('port', 8501)}:8501"
    ]
    
    # Add environment variables
    for key, value in config.get('environment', {}).items():
        cmd.extend(["-e", f"{key}={value}"])
    
    cmd.append("resdx-agent")
    
    subprocess.run(cmd, check=True)
    print("✅ Docker container deployed successfully!")


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy ResDex Agent")
    parser.add_argument("--environment", "-e", default="development", 
                       help="Deployment environment (development/staging/production)")
    parser.add_argument("--method", "-m", default="streamlit",
                       help="Deployment method (streamlit/docker)")
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.environment)
        
        if args.method == "streamlit":
            deploy_streamlit(config)
        elif args.method == "docker":
            deploy_docker(config)
        else:
            print(f"❌ Unknown deployment method: {args.method}")
            return 1
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())