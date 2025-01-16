import html
import re
from collections import OrderedDict
from urllib.parse import urlparse

import aiohttp


class ChallengeSolver:

    def __init__(self, resp: aiohttp.ClientResponse, resp_text: str):
        self.resp = resp
        self.resp_text = resp_text

    def solve_iuam_challenge(self, url, interpreter):
        try:
            form_payload = re.search(
                r'<form (?P<form>.*?="challenge-form" '
                r'action="(?P<challengeUUID>.*?'
                r'__cf_chl_f_tk=\S+)"(.*?)</form>)',
                self.resp_text,
                re.M | re.DOTALL
            ).groupdict()

            # if not all(key in formPayload for key in ['form', 'challengeUUID']):
            #     self.cloudscraper.simpleException(
            #         CloudflareIUAMError,
            #         "Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly."
            #     )

            payload = OrderedDict()
            for challenge_param in re.findall(r'^\s*<input\s(.*?)/>', form_payload['form'], re.M | re.S):
                input_payload = dict(re.findall(r'(\S+)="(\S+)"', challenge_param))
                if (input_payload_name := input_payload.get('name')) in ['r', 'jschl_vc', 'pass']:
                    payload.update({ input_payload_name: input_payload['value'] })

        except AttributeError:
            pass
            # self.cloudscraper.simpleException(
            #     CloudflareIUAMError,
            #     "Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly."
            # )

        else:
            try:
                netloc = self.resp.url.host + (f":{self.resp.url.port}" if self.resp.url.port else "")
                payload['jschl_answer'] = JavaScriptInterpreter.dynamicImport(
                    interpreter
                ).solveChallenge(self.resp_text, netloc)

            except Exception as e:
                pass
                # self.cloudscraper.simpleException(
                #     CloudflareIUAMError,
                #     f"Unable to parse Cloudflare anti-bots page: {getattr(e, 'message', e)}"
                # )

            else:
                unescaped_challenge_uuid = html.unescape(form_payload['challengeUUID'])
                post_challenge_url = f"{url.scheme}://{url.netloc}{unescaped_challenge_uuid}"
                return {
                    'url': post_challenge_url,
                    'data': payload
                }
