#!/usr/bin/env python3
"""
HuggingFace Papers Agent

An agent that scrapes papers from HuggingFace, downloads PDFs, generates summaries,
and analyzes relevance for Flywheel Product Line work.

Usage:
    python hf_paper_agent.py --month 2025-11  # Download papers from November 2025
    python hf_paper_agent.py                  # Download papers from current month
"""

import os
import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
import hashlib
import argparse


class Config:
    """Configuration for the paper agent"""
    BASE_DIR = Path(__file__).parent
    PAPERS_DIR = BASE_DIR / "papers"
    INDEX_FILE = BASE_DIR / "papers_index.md"
    TRACKER_FILE = BASE_DIR / "papers_tracker.json"
    HF_PAPERS_URL = "https://huggingface.co/papers"

    CATEGORIES = {
        "sales": "Relevant for sales teams, sales automation, lead scoring, pipeline management",
        "demand_generation": "Relevant for marketing, demand gen, lead generation, campaign optimization",
        "customer_success": "Relevant for CS teams, retention, expansion, health scoring, usage analytics",
        "customer_support": "Relevant for support teams, ticket automation, chatbots, help desk optimization",
        "solution_partners": "Relevant for partner enablement, integration opportunities, platform extensions"
    }


class PaperTracker:
    """Tracks downloaded papers to avoid duplicates"""

    def __init__(self, tracker_file: Path):
        self.tracker_file = tracker_file
        self.data = self._load()

    def _load(self) -> Dict:
        if self.tracker_file.exists():
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        return {"papers": {}}

    def _save(self):
        with open(self.tracker_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def is_downloaded(self, paper_id: str, month: str) -> bool:
        """Check if paper is already fully downloaded"""
        key = f"{month}/{paper_id}"
        return key in self.data["papers"] and self.data["papers"][key].get("status") == "complete"

    def mark_complete(self, paper_id: str, month: str, metadata: Dict):
        """Mark paper as successfully downloaded"""
        key = f"{month}/{paper_id}"
        self.data["papers"][key] = {
            "status": "complete",
            "downloaded_at": datetime.now().isoformat(),
            "metadata": metadata
        }
        self._save()

    def mark_failed(self, paper_id: str, month: str, error: str):
        """Mark paper download as failed"""
        key = f"{month}/{paper_id}"
        self.data["papers"][key] = {
            "status": "failed",
            "error": error,
            "attempted_at": datetime.now().isoformat()
        }
        self._save()


class HFPaperScraper:
    """Scrapes paper information from HuggingFace"""

    def __init__(self, use_selenium: bool = False):
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_monthly_papers(self, year: int, month: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch papers for a specific month from HuggingFace

        Returns list of dicts with: title, url, paper_id, authors, upvotes
        """
        url = f"{Config.HF_PAPERS_URL}?date={year}-{month:02d}"
        print(f"Fetching papers from: {url}")

        try:
            if self.use_selenium:
                html = self._fetch_with_selenium(url)
            else:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                html = response.content

            soup = BeautifulSoup(html, 'html.parser')
            papers = []

            # Strategy 1: Look for links with /papers/ pattern
            paper_links = soup.find_all('a', href=re.compile(r'/papers/\d+\.\d+'))

            seen_ids = set()
            for link in paper_links:
                try:
                    paper_url = link.get('href')
                    if not paper_url.startswith('http'):
                        paper_url = f"https://huggingface.co{paper_url}"

                    paper_id = paper_url.split('/papers/')[-1].split('?')[0].split('#')[0]

                    if paper_id in seen_ids:
                        continue
                    seen_ids.add(paper_id)

                    title = self._extract_title(link)
                    if not title or len(title) < 10:
                        continue

                    papers.append({
                        'title': title,
                        'url': paper_url,
                        'paper_id': paper_id
                    })

                    if limit and len(papers) >= limit:
                        break

                except Exception as e:
                    print(f"  Warning: Error extracting paper data: {e}")
                    continue

            if not papers:
                print("  Warning: No papers found using primary method")
                print("  This might mean the page structure has changed or requires JavaScript")
                print("  Try running with --use-selenium flag (requires selenium package)")

            print(f"Found {len(papers)} papers")
            return papers

        except Exception as e:
            print(f"Error fetching papers: {e}")
            return []

    def _fetch_with_selenium(self, url: str) -> str:
        """Fetch page content using Selenium for JavaScript rendering"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome(options=options)
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )

            time.sleep(2)
            html = driver.page_source
            driver.quit()

            return html

        except ImportError:
            print("Selenium not installed. Install with: pip install selenium")
            raise
        except Exception as e:
            print(f"Selenium error: {e}")
            raise

    def _extract_title(self, link_element) -> str:
        """Extract title from link element"""
        title = link_element.get_text(strip=True)
        if not title:
            parent = link_element.parent
            if parent:
                h_tags = parent.find_all(['h1', 'h2', 'h3', 'h4'])
                if h_tags:
                    title = h_tags[0].get_text(strip=True)
        return title

    def get_paper_details(self, paper_url: str) -> Dict:
        """
        Fetch detailed information from paper page including PDF link

        Returns dict with: pdf_url, abstract, github_url, etc.
        """
        try:
            response = self.session.get(paper_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            details = {
                'pdf_url': None,
                'arxiv_url': None,
                'github_url': None,
                'abstract': None
            }

            # Find PDF link - usually links to arXiv
            pdf_links = soup.find_all('a', href=re.compile('arxiv.org/pdf|arxiv.org/abs'))
            if pdf_links:
                arxiv_url = pdf_links[0].get('href')
                details['arxiv_url'] = arxiv_url
                # Convert abs link to pdf link
                if '/abs/' in arxiv_url:
                    details['pdf_url'] = arxiv_url.replace('/abs/', '/pdf/') + '.pdf'
                else:
                    details['pdf_url'] = arxiv_url

            # Find GitHub link
            github_links = soup.find_all('a', href=re.compile('github.com'))
            if github_links:
                details['github_url'] = github_links[0].get('href')

            # Find abstract
            abstract_div = soup.find('div', class_=re.compile('abstract')) or soup.find('p', class_=re.compile('abstract'))
            if abstract_div:
                details['abstract'] = abstract_div.get_text(strip=True)

            return details

        except Exception as e:
            print(f"Error fetching paper details: {e}")
            return {}


class PaperDownloader:
    """Downloads and extracts text from papers"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def download_pdf(self, pdf_url: str, save_path: Path) -> bool:
        """Download PDF file"""
        try:
            print(f"Downloading PDF from: {pdf_url}")
            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()

            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"PDF saved to: {save_path}")
            return True

        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return False

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            # Try using PyPDF2 if available
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = []
                    for page in reader.pages:
                        text.append(page.extract_text())
                    return '\n\n'.join(text)
            except ImportError:
                print("PyPDF2 not installed. Install with: pip install PyPDF2")
                return "[PDF text extraction requires PyPDF2 library]"

        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return "[Error extracting text from PDF]"


class PaperAnalyzer:
    """Analyzes papers for relevance and generates summaries"""

    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.use_ai = self.api_key is not None

    def analyze_paper(self, title: str, abstract: str, full_text: str) -> Dict:
        """
        Analyze paper and generate:
        - Summary
        - FPL relevance assessment
        - Startup opportunities
        """
        if self.use_ai:
            return self._analyze_with_ai(title, abstract, full_text)
        else:
            return self._analyze_without_ai(title, abstract)

    def _analyze_with_ai(self, title: str, abstract: str, full_text: str) -> Dict:
        """Use Claude API for analysis"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            # Handle None values
            title = title or "Untitled"
            abstract = abstract or "No abstract available"
            full_text = full_text or "No text extracted"

            # Truncate full text if too long
            text_sample = full_text[:10000] if len(full_text) > 10000 else full_text

            prompt = f"""Analyze this AI/ML research paper:

Title: {title}

Abstract: {abstract}

Text Sample: {text_sample}

Provide analysis in the following format:

## Summary
[2-3 paragraph summary of the paper's key contributions, methods, and results]

## FPL Relevance
Assess relevance for these areas (rate as High/Medium/Low/None and explain):
- Sales: [Assessment and reasoning]
- Demand Generation: [Assessment and reasoning]
- Customer Success: [Assessment and reasoning]
- Customer Support: [Assessment and reasoning]
- Solution Partners: [Assessment and reasoning]

## Startup Opportunities
[3-5 potential startup ideas or business applications based on this research]

## Overall FPL Value
[High/Medium/Low] - [Brief explanation of overall value for FPL teams]"""

            # Use the latest available Claude model
            # Try different models in order of preference
            models_to_try = [
                "claude-haiku-4-5-20251001"      # Claude 3 Haiku (budget)
            ]

            message = None
            last_error = None

            for model_id in models_to_try:
                try:
                    message = client.messages.create(
                        model=model_id,
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    print(f"    Using model: {model_id}")
                    break  # Success, exit loop
                except Exception as e:
                    last_error = e
                    if "404" not in str(e) and "not_found" not in str(e):
                        # If it's not a model not found error, don't try other models
                        raise
                    continue

            if message is None:
                raise Exception(f"No available models found. Last error: {last_error}")

            return {
                'summary': message.content[0].text,
                'ai_generated': True
            }

        except Exception as e:
            print(f"Error with AI analysis: {e}")
            return self._analyze_without_ai(title, abstract)

    def _analyze_without_ai(self, title: str, abstract: str) -> Dict:
        """Basic analysis without AI"""
        # Handle None values
        title = title or "Untitled"
        abstract = abstract or "No abstract available"

        # Simple keyword-based relevance detection
        text_lower = (title + " " + abstract).lower()

        relevance = {}
        for category, keywords_desc in Config.CATEGORIES.items():
            keywords = ['sales', 'marketing', 'customer', 'support', 'automation', 'analytics']
            score = sum(1 for kw in keywords if kw in text_lower)
            relevance[category] = "Medium" if score > 2 else "Low"

        return {
            'summary': f"# Summary\n\n{abstract}\n\n[Note: Install anthropic library and set ANTHROPIC_API_KEY for AI-generated summaries]",
            'relevance': relevance,
            'ai_generated': False
        }


class PaperManager:
    """Main orchestrator for the paper agent"""

    def __init__(self, use_selenium: bool = False):
        self.scraper = HFPaperScraper(use_selenium=use_selenium)
        self.downloader = PaperDownloader()
        self.analyzer = PaperAnalyzer()
        self.tracker = PaperTracker(Config.TRACKER_FILE)

        # Ensure directories exist
        Config.PAPERS_DIR.mkdir(exist_ok=True)

    def test_scraping(self, year: int, month: int):
        """Test scraping without downloading papers"""
        print(f"\n{'='*60}")
        print(f"TEST MODE: Fetching papers list for {year}-{month:02d}")
        print(f"{'='*60}\n")

        papers = self.scraper.get_monthly_papers(year, month, limit=5)

        if not papers:
            print("\nNo papers found. This could mean:")
            print("1. The page structure has changed")
            print("2. JavaScript is required (try --use-selenium)")
            print("3. Network or access issues")
            return

        print(f"\nSuccessfully found {len(papers)} papers (showing first 5):")
        print(f"{'='*60}\n")

        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title']}")
            print(f"   URL: {paper['url']}")
            print(f"   ID: {paper['paper_id']}")
            print()

        print("Test complete. Run without --test to download papers.")

    def process_month(self, year: int, month: int, force: bool = False, limit: Optional[int] = None):
        """Process all papers for a given month"""
        month_str = f"{year}-{month:02d}"
        print(f"\n{'='*60}")
        print(f"Processing papers for {month_str}")
        print(f"{'='*60}\n")

        # Create month directory
        month_dir = Config.PAPERS_DIR / month_str
        month_dir.mkdir(exist_ok=True)

        # Fetch papers
        papers = self.scraper.get_monthly_papers(year, month, limit=limit)

        if not papers:
            print("No papers found for this month")
            print("Try running with --use-selenium if the page requires JavaScript")
            return

        # Process each paper
        processed = 0
        skipped = 0
        failed = 0

        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}/{len(papers)}] Processing: {paper['title'][:60]}...")

            paper_id = paper['paper_id']

            # Check if already downloaded
            if not force and self.tracker.is_downloaded(paper_id, month_str):
                print(f"  ✓ Already downloaded, skipping")
                skipped += 1
                continue

            try:
                # Process the paper
                success = self._process_paper(paper, month_dir, month_str)
                if success:
                    processed += 1
                else:
                    failed += 1

                # Be respectful with rate limiting
                time.sleep(2)

            except Exception as e:
                print(f"  ✗ Error: {e}")
                self.tracker.mark_failed(paper_id, month_str, str(e))
                failed += 1

        print(f"\n{'='*60}")
        print(f"Summary: {processed} processed, {skipped} skipped, {failed} failed")
        print(f"{'='*60}\n")

        # Update index
        self._update_index()

    def _process_paper(self, paper: Dict, month_dir: Path, month_str: str) -> bool:
        """Process a single paper"""
        paper_id = paper['paper_id']

        # Sanitize filename
        safe_title = re.sub(r'[^\w\s-]', '', paper['title'])[:100]
        safe_title = re.sub(r'\s+', '-', safe_title)

        pdf_path = month_dir / f"{safe_title}.pdf"
        md_path = month_dir / f"{safe_title}.md"

        # Get paper details
        print(f"  Fetching details...")
        details = self.scraper.get_paper_details(paper['url'])

        if not details.get('pdf_url'):
            print(f"  ✗ No PDF URL found")
            self.tracker.mark_failed(paper_id, month_str, "No PDF URL found")
            return False

        # Download PDF
        print(f"  Downloading PDF...")
        if not self.downloader.download_pdf(details['pdf_url'], pdf_path):
            self.tracker.mark_failed(paper_id, month_str, "PDF download failed")
            return False

        # Extract text
        print(f"  Extracting text...")
        full_text = self.downloader.extract_text_from_pdf(pdf_path)
        if full_text is None:
            full_text = "[Text extraction failed]"

        # Analyze
        print(f"  Analyzing...")
        abstract = details.get('abstract', '') or ''
        analysis = self.analyzer.analyze_paper(paper['title'], abstract, full_text)

        # Create markdown file
        print(f"  Creating markdown...")
        self._create_markdown(paper, details, analysis, full_text, md_path)

        # Mark as complete
        metadata = {
            'title': paper['title'],
            'pdf_path': str(pdf_path.relative_to(Config.BASE_DIR)),
            'md_path': str(md_path.relative_to(Config.BASE_DIR)),
            'url': paper['url']
        }
        self.tracker.mark_complete(paper_id, month_str, metadata)

        print(f"  ✓ Complete")
        return True

    def _create_markdown(self, paper: Dict, details: Dict, analysis: Dict, full_text: str, md_path: Path):
        """Create markdown file for paper"""
        # Handle None values
        full_text = full_text or "[Text extraction failed]"
        summary = analysis.get('summary', '') or "No summary available"

        content = f"""# {paper['title']}

## Metadata
- **HuggingFace URL**: {paper['url']}
- **arXiv URL**: {details.get('arxiv_url', 'N/A')}
- **PDF**: [{md_path.stem}.pdf](./{md_path.stem}.pdf)
- **GitHub**: {details.get('github_url', 'N/A')}
- **Downloaded**: {datetime.now().strftime('%Y-%m-%d')}

## Abstract
{details.get('abstract', 'No abstract available')}

---

{summary}

---

## Full Paper Text

<details>
<summary>Click to expand full extracted text</summary>

{full_text[:50000]}

</details>

---

*Generated by HF Papers Agent*
"""

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _update_index(self):
        """Update the main index file"""
        print("Updating index...")

        # Collect all papers
        all_papers = []
        for month_dir in sorted(Config.PAPERS_DIR.iterdir(), reverse=True):
            if not month_dir.is_dir():
                continue

            for md_file in sorted(month_dir.glob("*.md")):
                # Extract title from first line of file
                with open(md_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    title = first_line.replace('# ', '')

                rel_path = md_file.relative_to(Config.BASE_DIR)
                all_papers.append((month_dir.name, title, rel_path))

        # Create index
        index_content = f"""# AI Papers Index

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Total papers: {len(all_papers)}

## Papers by Month

"""

        current_month = None
        for month, title, path in all_papers:
            if month != current_month:
                index_content += f"\n### {month}\n\n"
                current_month = month

            index_content += f"- [{title}]({path})\n"

        with open(Config.INDEX_FILE, 'w', encoding='utf-8') as f:
            f.write(index_content)

        print(f"Index updated: {Config.INDEX_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description='HuggingFace Papers Agent',
        epilog="""
Examples:
  python hf_paper_agent.py                      # Process current month
  python hf_paper_agent.py --month 2025-11      # Process November 2025
  python hf_paper_agent.py --test               # Test scraping without downloading
  python hf_paper_agent.py --limit 5            # Only process 5 papers
  python hf_paper_agent.py --use-selenium       # Use browser automation for dynamic content
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--month', type=str, help='Month to process (YYYY-MM format)', default=None)
    parser.add_argument('--force', action='store_true', help='Re-download already processed papers')
    parser.add_argument('--test', action='store_true', help='Test mode: only fetch and display paper list')
    parser.add_argument('--use-selenium', action='store_true', help='Use Selenium for JavaScript rendering (requires selenium package)')
    parser.add_argument('--limit', type=int, help='Limit number of papers to process', default=None)

    args = parser.parse_args()

    # Parse month
    if args.month:
        try:
            year, month = map(int, args.month.split('-'))
        except ValueError:
            print("Invalid month format. Use YYYY-MM (e.g., 2025-11)")
            return
    else:
        now = datetime.now()
        year, month = now.year, now.month

    # Run agent
    try:
        manager = PaperManager(use_selenium=args.use_selenium)

        if args.test:
            manager.test_scraping(year, month)
        else:
            manager.process_month(year, month, force=args.force, limit=args.limit)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
