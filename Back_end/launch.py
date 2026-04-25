#!/usr/bin/env python3
"""
Poker Bot Launcher - Cross-platform launcher script
Automatically checks dependencies and launches the hacker GUI
"""

import sys
import subprocess
import os
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header():
    """Print fancy header"""
    print(f"""
{CYAN}╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  ⚡ POKER BOT NEURAL INTERFACE - INITIALIZING ⚡          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝{RESET}
""")

def check_python_version():
    """Check Python version"""
    print(f"{CYAN}[*]{RESET} Checking Python version...")
    if sys.version_info < (3, 8):
        print(f"{RED}[ERROR]{RESET} Python 3.8+ required. You have {sys.version}")
        sys.exit(1)
    print(f"{GREEN}[✓]{RESET} Python {sys.version.split()[0]} OK")

def check_file(filename):
    """Check if file exists"""
    if not Path(filename).exists():
        print(f"{RED}[ERROR]{RESET} {filename} not found!")
        print(f"{YELLOW}[INFO]{RESET} Please run from the Back_end directory")
        sys.exit(1)

def install_package(package):
    """Install a pip package"""
    print(f"{YELLOW}[!]{RESET} Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])
    print(f"{GREEN}[✓]{RESET} {package} installed")

def check_dependencies():
    """Check and install missing dependencies"""
    print(f"{CYAN}[*]{RESET} Verifying dependencies...\n")
    
    packages = {
        'anthropic': 'Claude AI API',
        'easyocr': 'Optical Character Recognition',
        'PIL': 'Image processing',
        'mss': 'Screenshot capture',
        'python-dotenv': 'Environment configuration',
    }
    
    for package, description in packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"{GREEN}[✓]{RESET} {description:30} {CYAN}({package}){RESET}")
        except ImportError:
            print(f"{YELLOW}[!]{RESET} {description:30} {CYAN}({package}){RESET}")
            install_package(package)

def check_config():
    """Check .env configuration"""
    print(f"\n{CYAN}[*]{RESET} Checking configuration...")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print(f"{YELLOW}[WARNING]{RESET} .env file not found")
        print(f"{CYAN}[*]{RESET} Creating template...")
        
        env_content = """# Poker Bot Configuration
CLAUDE_API_KEY=your-api-key-here
ANALYSIS_INTERVAL=3
GOOGLE_APPLICATION_CREDENTIALS=./credentials/pokerbot-493518-65f60dcebe77.json
"""
        env_file.write_text(env_content)
        print(f"{YELLOW}[!]{RESET} Template created. Please add your CLAUDE_API_KEY")
        print(f"{CYAN}[*]{RESET} Get key at: https://console.anthropic.com")
        return False
    
    # Check for API key
    env_content = env_file.read_text()
    if 'your-api-key-here' in env_content or 'CLAUDE_API_KEY=' not in env_content:
        print(f"{RED}[ERROR]{RESET} CLAUDE_API_KEY not configured!")
        print(f"{CYAN}[*]{RESET} Edit .env and add your API key")
        print(f"{CYAN}[*]{RESET} Get key at: https://console.anthropic.com")
        return False
    
    print(f"{GREEN}[✓]{RESET} Configuration OK")
    return True

def launch_gui():
    """Launch the hacker GUI"""
    print(f"""
{CYAN}╔════════════════════════════════════════════════════════════╗
║                    SYSTEM READY                            ║
║              Launching Neural Interface...                 ║
╚════════════════════════════════════════════════════════════╝{RESET}
""")
    
    try:
        subprocess.run([sys.executable, "hacker_gui.py"], check=False)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[*]{RESET} Neural interface terminated by user")
    except Exception as e:
        print(f"{RED}[ERROR]{RESET} Failed to launch GUI: {e}")
        sys.exit(1)

def main():
    """Main launcher"""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print_header()
    
    # Checks
    check_python_version()
    check_file('hacker_gui.py')
    check_dependencies()
    
    if not check_config():
        print(f"\n{RED}[!]{RESET} Configuration incomplete. Exiting.")
        sys.exit(1)
    
    # Launch
    launch_gui()
    
    print(f"\n{YELLOW}[*]{RESET} Launcher closed.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[*]{RESET} Interrupted\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}[ERROR]{RESET} {e}\n")
        sys.exit(1)
