import pandas as pd
from playwright.async_api import async_playwright
import asyncio
import logging

class GoogleNewsLinkResolverOptimized:
    def __init__(self, max_pages=20, timeout=20, max_wait=5):
        """
        Initialize the link resolver with configurable parameters.

        :param max_pages: Maximum number of concurrent browser pages
        :param timeout: Page load timeout in seconds
        :param max_wait: Maximum wait time for redirection in seconds
        """
        self.max_pages = max_pages
        self.timeout = timeout * 1000  # Convert to milliseconds for Playwright
        self.max_wait = max_wait
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    async def _fetch_links(self, page, queue, results):
        while True:
            link = await queue.get()
            if link is None:  # Exit signal
                break

            try:
                await page.goto(link, timeout=self.timeout)
                start_time = asyncio.get_event_loop().time()

                # Wait until the URL does not start with 'https://news.google.com'
                while page.url.startswith("https://news.google.com"):
                    await page.wait_for_timeout(100)  # Wait for 0.1 second before checking again
                    if asyncio.get_event_loop().time() - start_time > self.max_wait:
                        break

                resolved_link = page.url
                if not resolved_link.startswith("https://news.google.com"):
                    results[link] = resolved_link  # Save the resolved link
                else:
                    results[link] = None  # Mark as unresolved if it still redirects
                self.logger.info(f"Resolved: {resolved_link}")
            except Exception as e:
                self.logger.error(f"Error resolving link: {e}")
                results[link] = None  # Mark as unresolved
            finally:
                queue.task_done()

    async def resolve_links(self, links):
        """
        Resolve multiple links concurrently.

        :param links: List of Google News links
        :return: Dictionary of rss links: resolved links
        """
        results = {}
        queue = asyncio.Queue()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # Create a pool of pages (max_pages pages)
            pages = [await context.new_page() for _ in range(self.max_pages)]

            # Start worker tasks for each page
            workers = [asyncio.create_task(self._fetch_links(page, queue, results)) for page in pages]

            # Add links to the queue
            for link in links:
                await queue.put(link)

            start_time = asyncio.get_event_loop().time()
            # Wait until all tasks are done
            await queue.join()

            # Stop workers
            for _ in range(self.max_pages):
                await queue.put(None)  # Send exit signal to workers

            await asyncio.gather(*workers)  # Ensure all workers finish

            total_time = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"Total time taken for resolving links: {total_time:.2f} seconds")

            failed_count = sum(1 for link, resolved_link in results.items() if resolved_link is None)
            self.logger.info(f"Total number of failed links: {failed_count}")

            await context.close()
            await browser.close()

        return results

    def resolve_links_sync(self, links):
        """
        Synchronous wrapper for resolving links.

        :param links: List of Google News links
        :return: Dictionary of rss links: resolved links
        """
        return asyncio.run(self.resolve_links(links))

# Example usage
if __name__ == "__main__":
    async def main():
        df = pd.read_excel(r"E:\Intern\Minerva\LLM API\TATA Motors.xlsx")
        links = list(df["Link"][:500])

        resolver = GoogleNewsLinkResolverOptimized(max_pages=20)
        resolved_links = await resolver.resolve_links(links)

        # for original_link, resolved_link in resolved_links.items():
        #     print(f"Resolved: {resolved_link}")

    asyncio.run(main())
