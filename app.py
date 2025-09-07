#!/usr/bin/env python3
import os
import re
from aws_cdk import App
from stacks.scraper_stack import ScraperStack

app = App()
context_scraper = app.node.try_get_context("scraper")  # pass --context scraper=sample_scraper

if not context_scraper:
    print("No --context scraper=<name> provided. To deploy a scraper: cdk deploy --app 'python3 app.py' --context scraper=sample_scraper ScraperStack-sample_scraper")
    app.synth()
    raise SystemExit(0)

scraper_name = context_scraper
scrapers_root = os.path.join(os.path.dirname(__file__), "scrapers")
scraper_path = os.path.join(scrapers_root, scraper_name)
if not os.path.isdir(scraper_path):
    raise SystemExit(f"Scraper folder not found: {scraper_path}")

stack_id = f"ScraperStack-{scraper_name.replace('_','-')}"

ScraperStack(app, stack_id, scraper_name=scraper_name, scraper_path=scraper_path)

app.synth()
