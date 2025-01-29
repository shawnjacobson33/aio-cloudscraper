import base64
import html
import re
from collections import OrderedDict

import aiohttp


class ChallengeSolver:

    def __init__(self, resp: aiohttp.ClientResponse, resp_text: str):
        self.resp = resp
        self.resp_text = resp_text

    def _template(self):
        try:
            js = re.search(
                r'setTimeout\(function\(\){\s+(.*?a\.value\s*=\s*\S+toFixed\(10\);)',
                self.resp_text,
                re.M | re.S
            ).group(1)

        except Exception:
            raise ValueError('Unable to identify Cloudflare IUAM Javascript on website.'
                             'Cloudflare may have changed their technique, or there may be a bug in the script.')

        js_env = '''String.prototype.italics=function(str) {{return "<i>" + this + "</i>";}};
            var subVars= {{{subVars}}};
            var document = {{
                createElement: function () {{
                    return {{ firstChild: {{ href: "https://{domain}/" }} }}
                }},
                getElementById: function (str) {{
                    return {{"innerHTML": subVars[str]}};
                }}
            }};
        '''

        try:
            js = js.replace(
                r"(setInterval(function(){}, 100),t.match(/https?:\/\//)[0]);",
                r"t.match(/https?:\/\//)[0];"
            )

            k = re.search(r" k\s*=\s*'(?P<k>\S+)';", self.resp_text).group('k')
            r = re.compile(r'<div id="{}(?P<id>\d+)">\s*(?P<jsfuck>[^<>]*)</div>'.format(k))

            sub_vars = ''
            for m in r.finditer(self.resp_text):
                sub_vars = '{}\n\t\t{}{}: {},\n'.format(sub_vars, k, m.group('id'), m.group('jsfuck'))
            sub_vars = sub_vars[:-2]

        except Exception:
            raise ValueError('Error extracting Cloudflare IUAM Javascript.'
                          'Cloudflare may have changed their technique, or there may be a bug in the script.')


        return '{}{}'.format(
            re.sub(
                r'\s{2,}',
                ' ',
                js_env.format(
                    domain=self.resp.host,
                    subVars=sub_vars
                ),
                re.MULTILINE | re.DOTALL
            ),
            js
        )

    def _interpret_javascript(self):
        js_payload = self._template()

        def atob(s):
            return base64.b64decode('{}'.format(s)).decode('utf-8')

        js2py.disable_pyimport()
        context = js2py.EvalJs({'atob': atob})
        result = context.eval(js_payload)

        return result

    def solve_iuam_challenge(self):
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
                payload['jschl_answer'] = self._interpret_javascript()

            except Exception as e:
                pass
                # self.cloudscraper.simpleException(
                #     CloudflareIUAMError,
                #     f"Unable to parse Cloudflare anti-bots page: {getattr(e, 'message', e)}"
                # )

            else:
                unescaped_challenge_uuid = html.unescape(form_payload['challengeUUID'])
                netloc = self.resp.url.host + (f":{self.resp.url.port}" if self.resp.url.port else "")
                post_challenge_url = f"{self.resp.url.scheme}://{netloc}{unescaped_challenge_uuid}"
                return {
                    'url': post_challenge_url,
                    'data': payload
                }
