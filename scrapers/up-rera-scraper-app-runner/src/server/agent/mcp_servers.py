#!/usr/bin/env python3
"""
UP RERA Projects List Scraper
Scrapes the projects list from https://www.up-rera.in/projects
Optimized for slow website with proper timeouts and retries
"""

import asyncio
import json
import re
import logging
from playwright.async_api import async_playwright
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any
from datetime import datetime
import sys

# Configure logging to stderr so it appears in MCP server logs
logging.basicConfig(
    level=logging.INFO,
    format='[MCP-SCRAPER] %(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

mcp = FastMCP("scrape_up_rera_projects_list")


@mcp.tool()
async def scrape_projects_list(max_projects: int = 50, timeout: int = 180) -> Dict[str, Any]:
    """
    Scrape UP RERA projects list from the main projects page.

    NOTE: Scraping is slow. 50 projects takes ~60-90 seconds. 
    Use smaller max_projects (10-20) for faster responses.

    Args:
        max_projects: Maximum number of projects to scrape (default: 50, recommended: 10-20 for speed)
        timeout: Page load timeout in seconds (default 180s for slow website)

    Returns:
        JSON response with structure:
        {
            "success": bool,
            "data": {
                "total_projects": int,
                "projects": [...],
                "run_id": str,
                "scraped_at": str
            },
            "error": str (only present on failure),
            "message": str
        }
    """
    # Generate unique run ID for file naming (avoid conflicts with parallel runs)
    import uuid
    run_id = str(uuid.uuid4())[:8]
    logger.info(
        f"Starting scrape_projects_list [run_id={run_id}]: max_projects={max_projects}, timeout={timeout}s")
    projects = []
    scrape_start_time = datetime.now()

    async with async_playwright() as p:
        logger.info('🚀 Launching browser...')
        browser = await p.chromium.launch(
            headless=True,  # Must be True for Docker/production
            slow_mo=0,  # No delay needed in headless mode
            args=[
                # Use /tmp instead of /dev/shm (limited in Docker)
                '--disable-dev-shm-usage',
                '--disable-gpu',  # Disable GPU to reduce memory
                '--no-sandbox',  # Required for Docker
                '--disable-setuid-sandbox',
                '--single-process',  # Use single process to reduce memory
            ]
        )

        context = await browser.new_context(
            # Smaller viewport to reduce memory
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # Increase default timeouts for slow website
        context.set_default_timeout(timeout * 1000)
        context.set_default_navigation_timeout(timeout * 1000)

        page = await context.new_page()

        try:
            logger.info(
                f'🔍 Navigating to UP RERA homepage (timeout: {timeout}s)...')
            logger.info('⏳ This may take a while due to slow website...')

            # Step 1: Go to homepage
            await page.goto('https://www.up-rera.in/index', wait_until='domcontentloaded', timeout=timeout * 1000)
            await page.wait_for_timeout(5000)
            logger.info('✅ Landed on homepage.')

            # Step 2: Find and click the "REGISTERED PROJECTS" link
            logger.info('🔗 Searching for "REGISTERED PROJECTS" link...')

            # Use page.click() with text selector (more robust than element handles)
            # This avoids element detachment issues from parallel runs
            clicked = False
            try:
                # Try clicking by text (handles dynamic DOM better)
                await page.click('text="Registered Projects"', timeout=10000)
                clicked = True
                logger.info('✅ Clicked link via text selector')
            except:
                try:
                    await page.click('text="REGISTERED PROJECTS"', timeout=10000)
                    clicked = True
                    logger.info('✅ Clicked link via text selector (uppercase)')
                except:
                    pass

            if not clicked:
                # Fallback to element handle approach
                logger.info(
                    '⚠️  Text selector failed, trying element handle approach...')
                all_links = await page.query_selector_all('a')
                for link in all_links:
                    try:
                        text = (await link.inner_text()).strip()
                        if text == 'Registered Projects' or text == 'REGISTERED PROJECTS':
                            await link.click()
                            clicked = True
                            logger.info(f'✅ Clicked link with text: "{text}"')
                            break
                    except:
                        continue

            if not clicked:
                raise Exception(
                    'Could not find or click "REGISTERED PROJECTS" link on homepage.')

            # Wait for navigation
            logger.info('⏳ Waiting for navigation after click...')
            # Give page time to navigate/load
            await page.wait_for_timeout(8000)

            # Step 3: Wait for projects list to appear
            logger.info('⏳ Waiting for projects list page to load...')
            # Wait for table or project list to appear
            try:
                await page.wait_for_selector('table, .project-list, .data-table, tbody tr', timeout=60000)
                logger.info('✅ Found table elements')
            except Exception as e1:
                logger.info(
                    f'⚠️  Table not found, trying alternative selectors... ({str(e1)[:50]})')
                try:
                    await page.wait_for_selector('body', timeout=30000)
                    await page.wait_for_timeout(10000)
                    logger.info(
                        '✅ Page body loaded, waiting for dynamic content...')
                except Exception as e2:
                    logger.info(
                        f'⚠️  Using fallback strategy ({str(e2)[:50]})')
                    await page.wait_for_timeout(15000)

            # Skip screenshot and HTML saving in production (causes browser crashes due to memory)
            # These are only useful for local debugging
            logger.info(
                'ℹ️  Skipping screenshot/HTML dump (memory optimization for production)')

            # Get page text for fallback extraction (but don't log it to save memory)
            page_text = ""
            try:
                page_text = await page.inner_text('body')
                logger.info(f'📝 Got page content ({len(page_text)} chars)')
            except Exception as e:
                logger.warning(f'⚠️  Could not get page text: {str(e)[:100]}')
                page_text = ""  # Continue anyway

            # Try to find project data with multiple strategies
            logger.info('🔍 Searching for project data...\n')

            # Strategy 1: Look for standard table structure
            # Target the specific projects table with ID grdPojDetail
            table_rows = await page.query_selector_all('#grdPojDetail tbody tr')
            logger.info(
                f'   Found {len(table_rows)} table rows in projects table')

            if table_rows:
                logger.info('📊 Extracting data from table rows...\n')

                # Process all rows or up to max_projects if specified
                rows_to_process = table_rows if max_projects is None else table_rows[
                    :max_projects]
                for idx, row in enumerate(rows_to_process):
                    try:
                        # Get all cells in the row
                        cells = await row.query_selector_all('td, th')

                        # Debug: Print first few rows
                        if idx < 5:
                            logger.info(
                                f'   Row {idx}: Found {len(cells)} cells')

                        # Skip header rows
                        if not cells or len(cells) < 2:
                            if idx < 5:
                                logger.info(
                                    f'   Row {idx}: Skipped (not enough cells)')
                            continue

                        # Extract text from cells
                        cell_texts = []
                        for cell in cells:
                            text = (await cell.inner_text()).strip()
                            cell_texts.append(text)

                        # Debug: Print first few rows' cell texts
                        if idx < 5:
                            logger.info(
                                f'   Row {idx} cells: {cell_texts[:4]}')

                        # Skip empty rows or header rows
                        if not cell_texts or all(not t for t in cell_texts):
                            if idx < 5:
                                logger.info(f'   Row {idx}: Skipped (empty)')
                            continue

                        # Check if this looks like a header row
                        first_cell_text = cell_texts[0].lower()
                        if any(keyword in first_cell_text for keyword in ['s.no', 'sr.', 'serial', 'project name', 'rera']):
                            logger.info(f'   Header row: {cell_texts[:3]}')
                            continue

                        # Look for links in the row
                        link_elements = await row.query_selector_all('a[href]')
                        detail_link = ''
                        rera_number = ''

                        for link in link_elements:
                            href = await link.get_attribute('href')
                            if href and ('Frm_View_Project_Details' in href or 'project' in href.lower()):
                                if href.startswith('http'):
                                    detail_link = href
                                else:
                                    detail_link = f'https://www.up-rera.in/{href.lstrip("/")}'

                                # Try to extract RERA number from link text
                                link_text = await link.inner_text()
                                rera_match = re.search(
                                    r'UPRERAPRJ\d+', link_text)
                                if rera_match:
                                    rera_number = rera_match.group(0)
                                break

                        # Build project object
                        # UP RERA table columns: S.No, Promoter Name, Project Name, RERA Reg.No., ProjectType, District, StartDate, EndDate, Registration Date, Details
                        project = {
                            'serial_no': cell_texts[0] if len(cell_texts) > 0 else '',
                            'promoter_name': cell_texts[1] if len(cell_texts) > 1 else '',
                            'project_name': cell_texts[2] if len(cell_texts) > 2 else '',
                            'rera_number': rera_number or (cell_texts[3] if len(cell_texts) > 3 else ''),
                            'project_type': cell_texts[4] if len(cell_texts) > 4 else '',
                            'district': cell_texts[5] if len(cell_texts) > 5 else '',
                            'start_date': cell_texts[6] if len(cell_texts) > 6 else '',
                            'end_date': cell_texts[7] if len(cell_texts) > 7 else '',
                            'registration_date': cell_texts[8] if len(cell_texts) > 8 else '',
                            'detail_link': detail_link,
                            'scraped_at': datetime.now().isoformat()
                        }

                        # Only add if we have meaningful data
                        if project['project_name'] or project['rera_number']:
                            projects.append(project)

                            if len(projects) % 10 == 0:
                                logger.info(
                                    f'✓ Extracted {len(projects)} projects...')

                    except Exception as e:
                        logger.info(f'⚠️  Error extracting row {idx}: {e}')
                        continue

            # Strategy 2: Look for divs/cards if table not found
            if not projects:
                logger.info('\n🔍 Trying card/div layout...')
                cards = await page.query_selector_all('.project-card, .project-item, div[data-project]')
                logger.info(f'   Found {len(cards)} card elements')

                cards_to_process = cards if max_projects is None else cards[:max_projects]
                for idx, card in enumerate(cards_to_process):
                    try:
                        card_text = await card.inner_text()

                        # Extract RERA number
                        rera_match = re.search(r'UPRERAPRJ\d+', card_text)
                        rera_number = rera_match.group(0) if rera_match else ''

                        # Extract link
                        link = await card.query_selector('a[href]')
                        detail_link = ''
                        if link:
                            href = await link.get_attribute('href')
                            if href:
                                detail_link = href if href.startswith(
                                    'http') else f'https://www.up-rera.in/{href.lstrip("/")}'

                        project = {
                            'rera_number': rera_number,
                            'detail_link': detail_link,
                            'raw_text': card_text[:200],  # First 200 chars
                            'scraped_at': datetime.now().isoformat()
                        }

                        if rera_number or detail_link:
                            projects.append(project)

                    except Exception as e:
                        logger.info(f'⚠️  Error extracting card {idx}: {e}')
                        continue

            # Strategy 3: Extract all RERA numbers from page text
            if not projects:
                logger.info('\n🔍 Extracting RERA numbers from page text...')
                rera_numbers = re.findall(r'UPRERAPRJ\d+', page_text)
                unique_rera = list(set(rera_numbers))
                logger.info(f'   Found {len(unique_rera)} unique RERA numbers')

                rera_to_process = unique_rera if max_projects is None else unique_rera[
                    :max_projects]
                for rera_num in rera_to_process:
                    projects.append({
                        'serial_no': '',
                        'promoter_name': '',
                        'project_name': '',
                        'rera_number': rera_num,
                        'project_type': '',
                        'district': '',
                        'start_date': '',
                        'end_date': '',
                        'registration_date': '',
                        'detail_link': f'https://www.up-rera.in/Frm_View_Project_Details.aspx?id={rera_num.replace("UPRERAPRJ", "")}',
                        'extracted_from': 'page_text',
                        'note': 'Only RERA number extracted. Visit detail_link for full information.',
                        'scraped_at': datetime.now().isoformat()
                    })

            logger.info(f'\n✅ Extraction complete!')
            logger.info(f'   Total projects found: {len(projects)}')

        except Exception as e:
            logger.error(f'\n❌ Error during scraping: {e}')
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(error_traceback)

            # Return error response
            scrape_end_time = datetime.now()
            duration_seconds = (
                scrape_end_time - scrape_start_time).total_seconds()

            return {
                "success": False,
                "data": {
                    "total_projects": 0,
                    "projects": [],
                    "run_id": run_id,
                    "scraped_at": scrape_end_time.isoformat(),
                    "duration_seconds": duration_seconds
                },
                "error": str(e),
                "error_details": error_traceback,
                "message": f"Scraping failed after {duration_seconds:.1f}s: {str(e)}"
            }

        finally:
            logger.info('\n🔒 Closing browser...')
            try:
                await context.close()
                await browser.close()
            except:
                pass  # Ignore errors during cleanup

    # Success response
    scrape_end_time = datetime.now()
    duration_seconds = (scrape_end_time - scrape_start_time).total_seconds()

    logger.info(
        f"✅ Completed scrape_projects_list: Returning {len(projects)} projects in {duration_seconds:.1f}s")

    return {
        "success": True,
        "data": {
            "total_projects": len(projects),
            "projects": projects,
            "run_id": run_id,
            "scraped_at": scrape_end_time.isoformat(),
            "duration_seconds": duration_seconds
        },
        "message": f"Successfully scraped {len(projects)} projects in {duration_seconds:.1f}s"
    }

if __name__ == "__main__":
    mcp.run(transport='stdio')
