import aiohttp

from cloudscraper.cloudflare import CloudFlare


class CloudScraper():
    
    def __init__(self):
        self.cloudflare = CloudFlare()
    
    async def perform_request(self, method, url, *args, **kwargs) -> aiohttp.ClientResponse:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, *args, **kwargs) as resp:
                return resp
            
    async def request(self, method, url, *args, **kwargs):
        resp = await self.perform_request(method, url, *args, **kwargs)
        resp_text = await resp.text()
        
        if self.cloudflare.is_captcha_challenge(resp):
            second_check_resp = await self.perform_request(method, url, *args, **kwargs)  # try one more time because somes sites only check if cfuid is populated
            if not self.cloudflare.is_captcha_challenge(second_check_resp):
                second_check_resp_text = await second_check_resp.text()
                return second_check_resp_text
                
    async def fetch(self, url: str, *args, **kwargs):
        return await self.request('GET', url, *args, **kwargs)

    async def post(self, url: str, *args, **kwargs):
        return await self.request('POST', url, *args, **kwargs)
            
        

    
    
