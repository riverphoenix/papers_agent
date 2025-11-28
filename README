# HuggingFace Papers Agent

Automated agent that downloads AI/ML research papers from HuggingFace, extracts content, generates summaries, and analyzes relevance for business applications.

## Features

- 📥 **Auto-download** papers from HuggingFace monthly listings
- 📄 **PDF extraction** with full text parsing
- 🤖 **AI-powered analysis** using Claude (summaries, startup opportunities, business relevance)
- 🏷️ **Smart tracking** to avoid re-downloading papers
- 📑 **Searchable index** of all papers organized by month
- 🔍 **GitHub link detection** when available

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key for AI analysis (optional but recommended)
export ANTHROPIC_API_KEY="your-key"

# Test it
python hf_paper_agent.py --test

# Download papers from current month
python hf_paper_agent.py

# Download from specific month
python hf_paper_agent.py --month 2025-11
```

## Usage

```bash
# Download with limit
python hf_paper_agent.py --limit 5

# Force re-download
python hf_paper_agent.py --force

# Use Selenium for JavaScript-heavy pages
python hf_paper_agent.py --use-selenium
```

## Output

```
papers/
├── 2025-11/
│   ├── paper-name.pdf          # Downloaded PDF
│   └── paper-name.md           # Analysis & summary
papers_index.md                  # Searchable index
papers_tracker.json              # Download tracking
```

## What You Get

Each paper includes:
- **Summary**: 2-3 paragraph overview of key contributions
- **Business Analysis**: Relevance assessment across multiple domains
- **Startup Opportunities**: 3-5 potential business ideas
- **Full Text**: Complete extracted paper content
- **Metadata**: Links to HuggingFace, arXiv, GitHub

## Requirements

- Python 3.8+
- `requests`, `beautifulsoup4`, `PyPDF2`, `anthropic`
- Optional: `selenium` for JavaScript rendering

## Configuration

The agent analyzes papers for:
- Sales automation
- Demand generation
- Customer success
- Customer support
- Solution partners

Customize categories in `Config.CATEGORIES` within the script.

## Tips

- Always test first: `--test` flag
- Use `--limit` for quick tests
- Set `ANTHROPIC_API_KEY` for best results
- Papers are organized by month automatically

## Example Output

```markdown
# Paper Title

## Summary
[AI-generated summary of research]

## Business Relevance
- Sales: [High/Medium/Low] - [Reasoning]
- Customer Success: [Assessment]
...

## Startup Opportunities
1. [Business idea based on research]
2. [Another opportunity]
...
```

## License

MIT

## Author

Tool for knowledge management and research tracking.

