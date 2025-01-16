import aiohttp
import re
import asyncio

from cloudscraper.utils import ChallengeIdentification, ChallengeSolver


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

    async def solve_challenge(self):
        if delay := self._get_delay():
            await asyncio.sleep(delay)
            submit_url = self.challenge_solver.solve_iuam_challenge()

            if submit_url:

                def updateAttr(obj, name, newValue):
                    try:
                        obj[name].update(newValue)
                        return obj[name]
                    except (AttributeError, KeyError):
                        obj[name] = {}
                        obj[name].update(newValue)
                        return obj[name]

                cloudflare_kwargs = deepcopy(kwargs)
                cloudflare_kwargs['allow_redirects'] = False
                cloudflare_kwargs['data'] = updateAttr(
                    cloudflare_kwargs,
                    'data',
                    submit_url['data']
                )

                urlParsed = urlparse(resp.url)
                cloudflare_kwargs['headers'] = updateAttr(
                    cloudflare_kwargs,
                    'headers',
                    {
                        'Origin': f'{urlParsed.scheme}://{urlParsed.netloc}',
                        'Referer': resp.url
                    }
                )

                challengeSubmitResponse = self.cloudscraper.request(
                    'POST',
                    submit_url['url'],
                    **cloudflare_kwargs
                )

                if challengeSubmitResponse.status_code == 400:
                    self.cloudscraper.simpleException(
                        CloudflareSolveError,
                        'Invalid challenge answer detected, Cloudflare broken?'
                    )

                # ------------------------------------------------------------------------------- #
                # Return response if Cloudflare is doing content pass through instead of 3xx
                # else request with redirect URL also handle protocol scheme change http -> https
                # ------------------------------------------------------------------------------- #

                if not challengeSubmitResponse.is_redirect:
                    return challengeSubmitResponse

                else:
                    cloudflare_kwargs = deepcopy(kwargs)
                    cloudflare_kwargs['headers'] = updateAttr(
                        cloudflare_kwargs,
                        'headers',
                        {'Referer': challengeSubmitResponse.url}
                    )

                    if not urlparse(challengeSubmitResponse.headers['Location']).netloc:
                        redirect_location = urljoin(
                            challengeSubmitResponse.url,
                            challengeSubmitResponse.headers['Location']
                        )
                    else:
                        redirect_location = challengeSubmitResponse.headers['Location']

                    return self.cloudscraper.request(
                        resp.request.method,
                        redirect_location,
                        **cloudflare_kwargs
                    )
    
    
            