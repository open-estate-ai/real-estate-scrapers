#!/usr/bin/env python3
from aws_cdk import App
from scraper_stack import ScraperStack
import os

app = App()
context_scraper = app.node.try_get_context("scraper")  # pass --context scraper=sample_scraper

if not context_scraper:
    print("No --context scraper=<name> provided. To deploy a scraper: cdk deploy --app 'python3 app.py' --context scraper=sample_scraper ScraperStack-sample_scraper")
    app.synth()
    raise SystemExit(0)

scraper_name = context_scraper
stack_id = f"OpenEstateAIScraperStack-{scraper_name}"
ScraperStack(app, stack_id, scraper_name=scraper_name)
app.synth()
