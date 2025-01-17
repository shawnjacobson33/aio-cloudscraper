from copy import deepcopy

import aiohttp
import re
import asyncio

from utils import ChallengeIdentification, ChallengeSolver
from utils.helpers import update_attr


class CloudFlare:

    def __init__(self, resp: aiohttp.ClientResponse, resp_text: str):
        self.resp = resp
        self.resp_text = resp_text

        self.challenge_identifier = ChallengeIdentification(resp, resp_text)
        self.challenge_solver = ChallengeSolver(resp, resp_text)

    def is_firewall_blocked(self) -> bool:
        try:
            return (
                self.resp.headers.get('Server', '').startswith('cloudflare')
                and self.resp.status == 403
                and re.search(
             r'<span class="cf-error-code">1020</span>',
                    self.resp_text,
                    re.M | re.DOTALL
                )
            )

        except AttributeError:
            pass

        return False

    def _get_delay(self) -> float | None:
        """CloudFlare requires a delay before solving a challenge"""
        # TODO: What is the significance of this search?
        try:
            return float(
                re.search(
                    r'submit\(\);\r?\n\s*},\s*([0-9]+)',
                    self.resp_text
                ).group(1)
            ) / float(1000)
        
        except Exception as e:
            print(f'Error: {e}')

    async def solve_challenge(self, **kwargs):
        if delay := self._get_delay():
            await asyncio.sleep(delay)
            if submit_url := self.challenge_solver.solve_iuam_challenge():
                cloudflare_kwargs = deepcopy(kwargs)
                cloudflare_kwargs['allow_redirects'] = False
                cloudflare_kwargs['data'] = update_attr(
                    cloudflare_kwargs,
                    'data',
                    submit_url['data']
                )

                netloc = self.resp.url.host + (f":{self.resp.url.port}" if self.resp.url.port else "")
                cloudflare_kwargs['headers'] = update_attr(
                    cloudflare_kwargs,
                    'headers',
                    {
                        'Origin': f'{self.resp.url.scheme}://{netloc}',
                        'Referer': self.resp.url
                    }
                )

                return submit_url['url'], cloudflare_kwargs

            raise ValueError('Failed to solve CloudFlare challenge')
    
    
            