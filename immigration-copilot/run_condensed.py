#!/usr/bin/env python3
"""
Run script for the condensed Immigration Copilot
"""

import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_condensed.py <mode>")
        print("Modes:")
        print("  cli     - Command-line interface")
        print("  web     - Web application (port 3000)")
        print("  o1      - O-1 specific web application")
        return

    mode = sys.argv[1]

    # Import the condensed module
    from immigration_copilot import main as run_app

    # Set mode and run
    sys.argv = ['immigration_copilot.py', mode]
    run_app()

if __name__ == '__main__':
    main()
