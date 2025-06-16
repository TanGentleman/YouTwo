# This file provides a simplified interface to the Vectara-Convex sync process
from src.yt_rag.backend import main_from_cli, test_convex_connection

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync Vectara documents to Convex")
    parser.add_argument("--max-docs", type=int, default=20, help="Maximum number of documents to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test", action="store_true", help="Just test the Convex connection")
    args = parser.parse_args()
    
    # Build sys.argv for the backend function
    sys.argv = ['']  # Script name
    if args.max_docs:
        sys.argv.extend(["--max-docs", str(args.max_docs)])
    if args.debug:
        sys.argv.append("--debug")
    if args.test:
        sys.argv.append("--test-connection")
        # Could call test_convex_connection() here
    
    # Run the backend process
    success = main_from_cli()
    exit(0 if success else 1)
