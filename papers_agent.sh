#!/bin/bash
# Convenient wrapper for HuggingFace Papers Agent

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}HuggingFace Papers Agent${NC}"
echo ""

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${BLUE}Note: ANTHROPIC_API_KEY not set. Will use basic analysis.${NC}"
    echo "For AI-powered analysis, set: export ANTHROPIC_API_KEY='your-key'"
    echo ""
fi

# Run the agent
python3 hf_paper_agent.py "$@"

# Show index after completion
if [ $? -eq 0 ] && [ -f papers_index.md ]; then
    echo ""
    echo -e "${GREEN}Papers index updated!${NC}"
    echo "View at: $SCRIPT_DIR/papers_index.md"
fi
