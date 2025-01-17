from copy import deepcopy
from urllib.parse import urlparse, urljoin

import aiohttp

from cloudflare import CloudFlare
from utils import update_attr


class CloudScraper:
    
    def __init__(self):
        pass

    @staticmethod
    async def perform_request(method, url, *args, **kwargs) -> aiohttp.ClientResponse:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, *args, **kwargs) as resp:
                if resp.status == 200:
                    return resp

                raise ValueError(f'Failed to fetch {url}. Status code: {resp.status}')

    @staticmethod
    def _get_redirect_location(challenge_submit_resp: aiohttp.ClientResponse):
        if challenge_submit_resp_location := challenge_submit_resp.headers.get('Location'):
            if not urlparse(challenge_submit_resp_location).netloc:
                redirect_location = urljoin(
                    str(challenge_submit_resp.url),
                    challenge_submit_resp.headers['Location']
                )
                return redirect_location

            return challenge_submit_resp_location

        raise ValueError('No redirect location found')

    async def request(self, method, url, *args, **kwargs) -> str:
        resp = await self.perform_request(method, url, *args, **kwargs)
        resp_text = await resp.text()

        cloudflare = CloudFlare(resp, resp_text)
        if cloudflare.challenge_identifier.is_captcha_challenge(resp):
            second_check_resp = await self.perform_request(method, url, *args, **kwargs)  # try one more time because somes sites only check if cfuid is populated
            if not cloudflare.challenge_identifier.is_captcha_challenge(second_check_resp):
                second_check_resp_text = await second_check_resp.text()
                return second_check_resp_text

            try:
                submit_url, cloudflare_kwargs = await cloudflare.solve_challenge(**kwargs)
                challenge_submit_resp = await self.perform_request(
                    'POST',
                    submit_url['url'],
                    **cloudflare_kwargs
                )

            except ValueError as e:
                print(f'Error: {e}')

            else:
                cloudflare_kwargs = deepcopy(kwargs)
                cloudflare_kwargs['headers'] = update_attr(
                    cloudflare_kwargs,
                    'headers',
                    {'Referer': challenge_submit_resp.url}
                )

                try:
                    redirect_location = self._get_redirect_location(challenge_submit_resp)

                    new_resp = await self.perform_request(
                        resp.request_info.method,
                        redirect_location,
                        **cloudflare_kwargs
                    )

                    return await new_resp.text()

                except ValueError as e:
                    print(f'Error: {e}')

    async def fetch(self, url: str, *args, **kwargs):
        return await self.request('GET', url, *args, **kwargs)

    async def post(self, url: str, *args, **kwargs):
        return await self.request('POST', url, *args, **kwargs)
            
        

    
    
