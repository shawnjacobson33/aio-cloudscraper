import aiohttp
import re
import asyncio


class CloudFlare:

    def __init__(self):
        pass
    
    
    @staticmethod
    def is_captcha_challenge(resp: aiohttp.ClientResponse, resp_text: str) -> bool:
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status == 403
                and re.search(
                    r'<span class="cf-error-code">1020</span>',
                    resp.text,
                    re.M | re.DOTALL
                )
                and re.search(r'/cdn-cgi/images/trace/(captcha|managed)/', resp_text, re.M | re.S)
                and re.search(
                    r'''<form .*?="challenge-form" action="/\S+__cf_chl_f_tk=''',
                    resp_text,
                    re.M | re.S
                )
            )
            
        except AttributeError:
            pass

        return False
    
    def _get_delay(resp_text: str) -> float | None:
        """CloudFlare requires a delay before solving a challenge"""
        # TODO: What is the significance of this search?
        try:
            return float(
                re.search(
                    r'submit\(\);\r?\n\s*},\s*([0-9]+)',
                    resp_text
                ).group(1)
            ) / float(1000)
        
        except Exception as e:
            print(f'Error: {e}')
        
    async def solve_challenge(self, resp: aiohttp.ClientResponse, resp_text: str):
        if delay := self._get_delay(resp_text):
            await asyncio.sleep(delay)
            
    
    
            