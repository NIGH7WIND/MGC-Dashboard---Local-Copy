import asyncio
from playwright.async_api import async_playwright
import logging
import time
import pandas as pd

class GoogleNewsLinkResolver:
    def __init__(self, max_concurrent_tasks=10, timeout=5, max_wait=5):
        """
        Initialize the link resolver with configurable parameters.
        
        :param max_concurrent_tasks: Maximum number of concurrent browser tasks
        :param timeout: Page load timeout in seconds
        :param max_wait: Maximum wait time for redirection in seconds
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.timeout = timeout * 1000  # Convert to milliseconds for Playwright
        self.max_wait = max_wait
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    async def _fetch_single_link(self, link):
        """
        Fetch the original link from a Google News URL.
        
        :param link: Google News link to resolve
        :return: Resolved original link or None if failed
        """
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(link, timeout=self.timeout)
                
                redirected_url = page.url
                start_time = asyncio.get_event_loop().time()
                
                while redirected_url.startswith('https://news.google.com'):
                    await asyncio.sleep(0.5)
                    redirected_url = page.url
                    
                    if asyncio.get_event_loop().time() - start_time > self.max_wait:
                        break
                self.logger.info(f"Resolved link: {redirected_url}")
                await browser.close()
                return redirected_url
        except Exception as e:
            self.logger.error(f"Error resolving link: {e}")
            return None
        finally:
            if browser:
                await browser.close()

    async def resolve_links(self, links):
        """
        Resolve multiple links concurrently.
        
        :param links: List of Google News links
        :return: Dictionary of rss links: resolved links
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        async def bounded_fetch(link):
            async with semaphore:
                return await self._fetch_single_link(link)
        
        tasks = [bounded_fetch(link) for link in links]
        results = await asyncio.gather(*tasks)
        
        return dict(zip(links, results))

    def resolve_links_sync(self, links):
        """
        Synchronous wrapper for resolving links.
        
        :param links: List of Google News links
        :return: Dictionary of original links
        """
        return asyncio.run(self.resolve_links(links))

# # Example usage
# async def main():
#     df = pd.read_excel(r"E:\Intern\Minerva\LLM API\TATA Motors.xlsx")
#     links = list(df["Link"][:100])
    
#     start_time = time.time()
#     resolver = GoogleNewsLinkResolver(max_concurrent_tasks=20)
#     resolved_links = await resolver.resolve_links(links)
    
#     for original_link, resolved_link in resolved_links.items():
#         print(f"Resolved: {resolved_link}")
#     print("Total time taken: ", time.time()-start_time)
# # If running as a script
# if __name__ == "__main__":
#     asyncio.run(main())