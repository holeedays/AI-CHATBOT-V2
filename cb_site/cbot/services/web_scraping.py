import sys
import asyncio
# this is just a fix for django channels and playwright's chromium launcher, we have to implement it in
# the asgi.py file in our root and manage.py
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class WebScraper():
    def __init__(self) -> None:
        pass

    # removes miscellaneous tags from given html 
    def _remove_unwanted_tags(self, html_content: str, unwanted_tags: list[str] = ["script", "style"]) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')

        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()

        return str(soup)
    
    # extract given tags from given html
    def _extract_tags(self, 
                      html_content: str, 
                      tags: list[str]) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')
        text_parts: list[str] = []

        for tag in tags:
            elements = soup.find_all(tag)
            for element in elements:
                # If the tag is a link (a tag), append its href as well
                if tag == "a":
                    href = element.get('href')
                    if href:
                        text_parts.append(f"{element.get_text()} ({href})")
                    else:
                        text_parts.append(element.get_text())
                else:
                    text_parts.append(element.get_text())

        return ' '.join(text_parts)
    
    # remove whitespaces, redundant lines, etc...
    def _remove_unecssesary_lines(self, content: str) -> str:
        # Split content into lines
        lines = content.split("\n")

        # Strip whitespace for each line
        stripped_lines = [line.strip() for line in lines]

        # Filter out empty lines
        non_empty_lines = [line for line in stripped_lines if line]

        # Remove duplicated lines (while preserving order)
        seen: set[str] = set()
        deduped_lines = [line for line in non_empty_lines if not (
            line in seen or seen.add(line))]

        # Join the cleaned lines without any separators (remove newlines)
        cleaned_content = "".join(deduped_lines)

        return cleaned_content

    # actual scraper method
    # more foolproof than just extracting html contents with beautiful soup alone b/c some website prevents bot behavior;
    # playwright is slightly more in tune
    async def ascrape_playwright(self, 
                                 url: str, 
                                 tags: list[str] = ["h1", "h2", "h3", "h4", "span", "p", "div"]) -> str:
        import threading
        import asyncio
        from concurrent.futures import Future

        # This inner function will run in a separate thread
        def run_in_thread(url: str, tags: list[str], future: Future):
            # Create a NEW event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Force ProactorEventLoop if on Windows; idk why on my pc normal wsgi is activating rather than the asgi
            # interface, which is preventing playwright from working; also I recommend running 'playwright install'
            # to install the chromium interface too
            if sys.platform == 'win32':
                # We can't easily change the loop type once created, 
                # but we can try to create a Proactor one specifically.
                loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
                asyncio.set_event_loop(loop)

            # our actual scraping method
            async def internal_scrape():
                print(f"Scraper thread event loop: {type(asyncio.get_running_loop())}")
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    try:
                        page = await browser.new_page()
                        await page.goto(url)
                        page_source = await page.content()
                        results = self._remove_unecssesary_lines(self._extract_tags(self._remove_unwanted_tags(
                            page_source), tags))
                        return results
                    except Exception as e:
                        return f"Error: {e}"
                    finally:
                        await browser.close()

            try:
                result = loop.run_until_complete(internal_scrape())
                if not future.cancelled():
                    future.set_result(result)
            except Exception as e:
                if not future.cancelled():
                    future.set_exception(e)
            finally:
                loop.close()

        # Execute the scraper in a separate thread to ensure it has its own Proactor loop
        print("Delegating scraping to a Proactor-friendly thread...")
        scraping_future = Future()
        thread = threading.Thread(target=run_in_thread, args=(url, tags, scraping_future))
        thread.start()
        
        # Wait for the thread to finish and return the result
        return await asyncio.wrap_future(scraping_future)
