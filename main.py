"""AITAS - AI Terminal Assistant System
Entry point for the CLI application
"""
import sys
from cli.app import AITASCLI


def main():
    """Main entry point"""
    try:
        # Create CLI instance
        app = AITASCLI()

        # Initialize model and components
        app.initialize()

        # Run main loop
        app.run()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()