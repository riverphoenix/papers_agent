# HuggingFace Papers Agent

An intelligent agent that automatically scrapes AI/ML papers from HuggingFace, downloads PDFs, extracts content, generates summaries, and analyzes relevance for Flywheel Product Line (FPL) work areas.

## Features

- **Automated Paper Discovery**: Scrapes papers from HuggingFace's monthly listings
- **PDF Download**: Downloads paper PDFs from arXiv
- **Text Extraction**: Extracts full text from PDFs for analysis
- **AI-Powered Analysis**: Uses Claude API to generate summaries and analyze relevance
- **FPL Relevance Assessment**: Evaluates papers across five key areas:
  - Sales
  - Demand Generation
  - Customer Success
  - Customer Support
  - Solution Partners
- **Startup Opportunities**: Identifies potential business applications
- **Duplicate Detection**: Tracks downloaded papers to avoid re-processing
- **Index Maintenance**: Maintains a searchable index of all papers

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `PyPDF2` - PDF text extraction
- `anthropic` - Claude API for AI analysis (optional but recommended)

### 2. Configure API Key (Optional but Recommended)

For AI-powered analysis, set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Without this, the agent will still work but will generate basic summaries instead of AI-powered analysis.

## Usage

### Download Papers from Current Month

```bash
python hf_paper_agent.py
```

### Download Papers from a Specific Month

```bash
python hf_paper_agent.py --month 2025-11
python hf_paper_agent.py --month 2024-12
```

### Force Re-download of Papers

```bash
python hf_paper_agent.py --month 2025-11 --force
```

## Output Structure

```
/Users/dsotiriou/Documents/Python/Claude/
├── papers/
│   ├── 2025-11/
│   │   ├── paper-title-1.pdf
│   │   ├── paper-title-1.md
│   │   ├── paper-title-2.pdf
│   │   ├── paper-title-2.md
│   │   └── ...
│   ├── 2025-10/
│   └── ...
├── papers_index.md          # Main searchable index
├── papers_tracker.json      # Download tracking
└── hf_paper_agent.py        # The agent script
```

## Markdown File Format

Each paper gets a markdown file with:

```markdown
# Paper Title

## Metadata
- HuggingFace URL
- arXiv URL
- PDF link
- GitHub repository (if available)
- Download date

## Abstract
[Paper abstract]

## Summary
[AI-generated summary of key contributions]

## FPL Relevance
Assessment for each area:
- Sales: [High/Medium/Low] - [Reasoning]
- Demand Generation: [Assessment]
- Customer Success: [Assessment]
- Customer Support: [Assessment]
- Solution Partners: [Assessment]

## Startup Opportunities
[Potential business applications]

## Overall FPL Value
[High/Medium/Low] - [Explanation]

## Full Paper Text
[Complete extracted text]
```

## Integration with Your Notes

The agent automatically creates and maintains `papers_index.md` with links to all downloaded papers. You can:

1. **Link from your Obsidian vault**:
   ```markdown
   See [[../papers_index|AI Papers Index]]
   ```

2. **Copy to your vault**:
   ```bash
   ln -s /Users/dsotiriou/Documents/Python/Claude/papers ~/Documents/Personal/Notes/papers
   ```

3. **Reference specific papers**:
   Papers are organized by month and can be referenced in your notes.

## Advanced Usage

### Tracking System

The agent maintains `papers_tracker.json` to track:
- Successfully downloaded papers
- Failed downloads with error messages
- Download timestamps
- Metadata for each paper

### Rate Limiting

The agent includes automatic rate limiting (2-second delay between papers) to be respectful to HuggingFace and arXiv servers.

### Error Handling

- Network errors are caught and logged
- Failed downloads are tracked but don't stop the batch
- PDF extraction errors are handled gracefully
- Summary continues at the end showing: processed, skipped, failed

## Customization

### Modify FPL Categories

Edit `Config.CATEGORIES` in `hf_paper_agent.py`:

```python
CATEGORIES = {
    "sales": "Description...",
    "your_category": "Description...",
}
```

### Adjust Analysis Prompt

Modify `PaperAnalyzer._analyze_with_ai()` method to customize how papers are analyzed.

### Change Output Structure

Modify `PaperManager._create_markdown()` to customize markdown format.

## Troubleshooting

### No papers found
- Check if HuggingFace page structure has changed
- Verify network connectivity
- Try a different month

### PDF download fails
- Some papers may not have PDFs available
- arXiv links may be temporarily unavailable
- Check internet connection

### Text extraction fails
- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Some PDFs may be scanned images without extractable text

### AI analysis not working
- Verify ANTHROPIC_API_KEY is set
- Check API key is valid
- Ensure anthropic package is installed

## Example Workflow

```bash
# Process current month
python hf_paper_agent.py

# Process last 3 months
python hf_paper_agent.py --month 2025-11
python hf_paper_agent.py --month 2025-10
python hf_paper_agent.py --month 2025-09

# View index
cat papers_index.md

# Read a specific paper
open papers/2025-11/interesting-paper.md
```

## Integration Ideas

1. **Daily Cron Job**: Run automatically to catch new papers
2. **Slack Notifications**: Alert when high-value papers are found
3. **Team Sharing**: Share the papers directory with your team
4. **Research Reports**: Generate monthly summaries of relevant papers
5. **Trend Analysis**: Track topics over time using the index

## Future Enhancements

Potential improvements to consider:

- [ ] Add filtering by topics/keywords
- [ ] Email notifications for high-relevance papers
- [ ] Integration with paper reading services
- [ ] Citation tracking
- [ ] Related papers recommendations
- [ ] Export to Notion, Roam, or other tools
- [ ] Better PDF parsing for complex layouts
- [ ] Support for papers from other sources (arXiv directly, OpenReview, etc.)

## License

Personal use tool for Dimitris Sotiriou's knowledge management.
