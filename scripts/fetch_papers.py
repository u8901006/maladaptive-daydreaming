#!/usr/bin/env python3
"""
Fetch latest maladaptive daydreaming research papers from PubMed E-utilities API.
Uses keywords from the MD Research Toolkit for targeted searches.
Only fetches papers from the last 7 days that haven't been summarized yet.
"""

import json
import sys
import argparse
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote_plus

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

SEARCH_QUERIES = [
    '("maladaptive daydreaming"[Title/Abstract] OR "maladaptive daydreaming disorder"[Title/Abstract] OR "daydreaming disorder"[Title/Abstract] OR "problematic daydreaming"[Title/Abstract] OR "immersive daydreaming"[Title/Abstract] OR "excessive daydreaming"[Title/Abstract] OR "compulsive fantasizing"[Title/Abstract] OR "pathological fantasizing"[Title/Abstract])',
    '("Maladaptive Daydreaming Scale"[Title/Abstract] OR MDS-16[Title/Abstract] OR MDS-14[Title/Abstract] OR SCIMD[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND (dissociation[Title/Abstract] OR dissociative[Title/Abstract] OR trauma[Title/Abstract] OR PTSD[Title/Abstract] OR "childhood trauma"[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND (ADHD[Title/Abstract] OR "attention-deficit/hyperactivity disorder"[Title/Abstract] OR inattention[Title/Abstract] OR "mind wandering"[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND ("obsessive-compulsive"[Title/Abstract] OR OCD[Title/Abstract] OR compulsivity[Title/Abstract] OR craving[Title/Abstract] OR "loss of control"[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND ("default mode network"[Title/Abstract] OR neuroimaging[Title/Abstract] OR "functional connectivity"[Title/Abstract] OR "mental imagery"[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND ("problematic internet use"[Title/Abstract] OR "social media"[Title/Abstract] OR gaming[Title/Abstract] OR parasocial[Title/Abstract] OR "celebrity worship"[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND (treatment[Title/Abstract] OR intervention[Title/Abstract] OR psychotherapy[Title/Abstract] OR CBT[Title/Abstract] OR mindfulness[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND (adolescent[Title/Abstract] OR youth[Title/Abstract] OR student[Title/Abstract] OR "young adult"[Title/Abstract] OR school[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND (depression[Title/Abstract] OR anxiety[Title/Abstract] OR "emotion regulation"[Title/Abstract] OR loneliness[Title/Abstract] OR shame[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND (behavioral addiction[Title/Abstract] OR "behavioral addiction"[Title/Abstract] OR compulsivity[Title/Abstract] OR urge[Title/Abstract] OR withdrawal[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND (autism[Title/Abstract] OR autistic[Title/Abstract] OR ASD[Title/Abstract] OR "autistic traits"[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND (fantasy proneness[Title/Abstract] OR absorption[Title/Abstract] OR escapism[Title/Abstract] OR "experiential avoidance"[Title/Abstract])',
    '("maladaptive daydreaming"[Title/Abstract]) AND ("online community"[Title/Abstract] OR stigma[Title/Abstract] OR "self-diagnosis"[Title/Abstract] OR "lived experience"[Title/Abstract] OR fandom[Title/Abstract])',
]

HEADERS = {"User-Agent": "MDResearchBot/1.0 (maladaptive daydreaming research aggregator)"}


def load_summarized_pmids(docs_dir: str) -> set:
    summarized = set()
    if not os.path.isdir(docs_dir):
        return summarized
    cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=7)
    for fname in os.listdir(docs_dir):
        if not fname.startswith("md-report-") or not fname.endswith(".html"):
            continue
        date_str = fname.replace("md-report-", "").replace(".html", "")
        try:
            fdate = datetime.strptime(date_str, "%Y-%m-%d").replace(
                tzinfo=timezone(timedelta(hours=8))
            )
            if fdate < cutoff:
                continue
        except ValueError:
            continue
        fpath = os.path.join(docs_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            for pmid in re.findall(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", content):
                summarized.add(pmid)
        except Exception:
            pass
    return summarized


def search_papers(query: str, retmax: int = 50, days: int = 7) -> list:
    lookback = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    date_filter = f' AND "{lookback}"[Date - Publication] : "3000"[Date - Publication]'
    full_query = query + date_filter
    params = f"?db=pubmed&term={quote_plus(full_query)}&retmax={retmax}&sort=date&retmode=json"
    url = PUBMED_SEARCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[ERROR] PubMed search failed: {e}", file=sys.stderr)
        return []


def fetch_details(pmids: list) -> list:
    if not pmids:
        return []
    ids = ",".join(pmids)
    params = f"?db=pubmed&id={ids}&retmode=xml"
    url = PUBMED_FETCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=60) as resp:
            xml_data = resp.read().decode()
    except Exception as e:
        print(f"[ERROR] PubMed fetch failed: {e}", file=sys.stderr)
        return []

    papers = []
    try:
        root = ET.fromstring(xml_data)
        for article in root.findall(".//PubmedArticle"):
            medline = article.find(".//MedlineCitation")
            art = medline.find(".//Article") if medline else None
            if art is None:
                continue

            title_el = art.find(".//ArticleTitle")
            title = (
                (title_el.text or "").strip()
                if title_el is not None and title_el.text
                else ""
            )
            if not title:
                title = "".join(title_el.itertext()).strip() if title_el is not None else ""

            abstract_parts = []
            for abs_el in art.findall(".//Abstract/AbstractText"):
                label = abs_el.get("Label", "")
                text = "".join(abs_el.itertext()).strip()
                if label and text:
                    abstract_parts.append(f"{label}: {text}")
                elif text:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)[:2000]

            journal_el = art.find(".//Journal/Title")
            journal = (
                (journal_el.text or "").strip()
                if journal_el is not None and journal_el.text
                else ""
            )

            pub_date = art.find(".//PubDate")
            date_str = ""
            if pub_date is not None:
                year = pub_date.findtext("Year", "")
                month = pub_date.findtext("Month", "")
                day = pub_date.findtext("Day", "")
                parts = [p for p in [year, month, day] if p]
                date_str = " ".join(parts)

            pmid_el = medline.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            authors = []
            for author in art.findall(".//AuthorList/Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())
            author_str = ", ".join(authors[:5])
            if len(authors) > 5:
                author_str += " et al."

            keywords = []
            for kw in medline.findall(".//KeywordList/Keyword"):
                if kw.text:
                    keywords.append(kw.text.strip())

            doi = ""
            for aid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = (aid.text or "").strip()
                    break

            papers.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "authors": author_str,
                    "journal": journal,
                    "date": date_str,
                    "abstract": abstract,
                    "url": link,
                    "doi": doi,
                    "keywords": keywords,
                }
            )
    except ET.ParseError as e:
        print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)

    return papers


def main():
    parser = argparse.ArgumentParser(description="Fetch MD papers from PubMed")
    parser.add_argument("--days", type=int, default=7, help="Lookback days")
    parser.add_argument("--max-papers", type=int, default=50, help="Max papers to fetch")
    parser.add_argument("--output", default="papers.json", help="Output file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--docs-dir", default="docs", help="Docs dir for dedup check")
    args = parser.parse_args()

    summarized = load_summarized_pmids(args.docs_dir)
    print(f"[INFO] Found {len(summarized)} already-summarized PMIDs in last 7 days", file=sys.stderr)

    all_pmids = set()
    for i, query in enumerate(SEARCH_QUERIES):
        print(f"[INFO] Running query {i+1}/{len(SEARCH_QUERIES)}...", file=sys.stderr)
        pmids = search_papers(query, retmax=args.max_papers, days=args.days)
        all_pmids.update(pmids)
        print(f"  -> Found {len(pmids)} PMIDs (total unique: {len(all_pmids)})", file=sys.stderr)

    new_pmids = [p for p in all_pmids if p not in summarized]
    print(f"[INFO] Total unique: {len(all_pmids)}, New (not in last 7 days): {len(new_pmids)}", file=sys.stderr)

    if not new_pmids:
        print("[INFO] No new papers found", file=sys.stderr)
        output_data = {
            "date": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
            "count": 0,
            "papers": [],
        }
    else:
        pmids_to_fetch = new_pmids[:args.max_papers]
        papers = fetch_details(pmids_to_fetch)
        print(f"[INFO] Fetched details for {len(papers)} papers", file=sys.stderr)

        output_data = {
            "date": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
            "count": len(papers),
            "papers": papers,
        }

    out_str = json.dumps(output_data, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(out_str)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_str)
        print(f"[INFO] Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
