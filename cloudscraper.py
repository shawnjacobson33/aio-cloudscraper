import asyncio
from copy import deepcopy
from urllib.parse import urlparse, urljoin

import aiohttp

from cloudflare import CloudFlare
from utils import update_attr


class CloudScraper:
    
    def __init__(self):
        pass

    @staticmethod
    async def perform_request(method, url, *args, **kwargs) -> tuple[aiohttp.ClientResponse, str]:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, *args, **kwargs) as resp:
                resp_text = await resp.text()
                return resp, resp_text

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
        resp, resp_text = await self.perform_request(method, url, *args, **kwargs)
        cloudflare = CloudFlare(resp, resp_text)
        if cloudflare.challenge_identifier.is_captcha_challenge():
            second_check_resp, second_check_resp_text = await self.perform_request(
                method, url, *args, **kwargs)  # try one more time because somes sites only check if cfuid is populated
            if not cloudflare.challenge_identifier.is_captcha_challenge(second_check_resp):
                return second_check_resp_text

            try:
                submit_url, cloudflare_kwargs = await cloudflare.solve_challenge(**kwargs)
                challenge_submit_resp, _ = await self.perform_request(
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

                    new_resp, new_resp_text = await self.perform_request(
                        resp.request_info.method,
                        redirect_location,
                        **cloudflare_kwargs
                    )

                    return new_resp_text

                except ValueError as e:
                    print(f'Error: {e}')

        return resp_text

    async def fetch(self, url: str, *args, **kwargs):
        return await self.request('GET', url, *args, **kwargs)

    async def post(self, url: str, *args, **kwargs):
        return await self.request('POST', url, *args, **kwargs)


async def main():
    scraper = CloudScraper()
    await scraper.fetch(
        url='https://api.prizepicks.com/projections?league_id=9&per_page=250&single_stat=true&in_game=true&state_code=WI&game_mode=pickem',
        cookies={
            'ajs_anonymous_id': '0c20e023-4ac3-4d2a-aa22-72452ed28059',
            '_fbp': 'fb.1.1722653625319.566404622364524062',
            '_scid': '64da9e25-cae9-4b1f-bf6e-282a3702099a',
            '__podscribe_prizepicks_referrer': '_',
            '__podscribe_prizepicks_landing_url': 'https://www.prizepicks.com/',
            '__podscribe_did': 'pscrb_93729ef9-6531-4397-dfb2-900057db982e',
            'afUserId': '5e932583-c2bb-4461-98fa-1b5e1b1a26c7-p',
            '_pxvid': '9aea1505-5143-11ef-af3c-1c7e40392ae3',
            '__pxvid': '9b130b7a-5143-11ef-ba03-0242ac120002',
            'intercom-device-id-qmdeaj0t': 'bfcbefbf-d1bb-4f30-b3e9-a1cbcceee5b1',
            'intercom-id-qmdeaj0t': 'f103cbcc-a5cf-4058-87e2-cd6084dc9008',
            '_sp_id.9177': '4472dc67-cfda-4631-b867-1ffe8e11427e.1722653625.22.1724083321.1724080125.7cebba50-8ca3-4d4e-a40d-78f33f2c98fc',
            'ab.storage.deviceId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917': '%7B%22g%22%3A%228e0de1ba-3a8b-8ad7-d3ca-7ece02039dd6%22%2C%22c%22%3A1722457830004%2C%22l%22%3A1726714699655%7D',
            'ab.storage.userId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917': '%7B%22g%22%3A%225f67121e-cc2c-4c3b-aca0-7f9a9ebc8f96%22%2C%22c%22%3A1722457830003%2C%22l%22%3A1726714699655%7D',
            'ab.storage.sessionId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917': '%7B%22g%22%3A%2256cb5c53-3c38-e6d2-9c9e-45ecb1b28a22%22%2C%22e%22%3A1726716499693%2C%22c%22%3A1726714699654%2C%22l%22%3A1726714699693%7D',
            '_tt_enable_cookie': '1',
            '_vwo_uuid_v2': 'D87EAA71160DE47A379FAECEC3EB7A00C|22637891b01e5ec2a6540cd2f175a225',
            '_gcl_au': '1.1.558188604.1730824779',
            '_ttp': 'X7DD4QodZBUUH_mkQI9ifF0bdyp.tt.1',
            'intercom-session-qmdeaj0t': '',
            'rl_anonymous_id': 'RS_ENC_v3_IjQ0MWQwNzQzLTZhYjYtNGVjNC04NTBjLWQwMTllY2Q4NmQ3YyI%3D',
            'rl_page_init_referrer': 'RS_ENC_v3_IiRkaXJlY3Qi',
            'rs_ga': 'GA1.1.441d0743-6ab6-4ec4-850c-d019ecd86d7c',
            'pxcts': '5caf9d90-cbf0-11ef-b9e7-785b214f4ee8',
            'AF_SYNC': '1736967189581',
            '_sctr': '1%7C1737007200000',
            '_rdt_em': '0000000000000000000000000000000000000000000000000000000000000001',
            '_clck': 'xtr0pf%7C2%7Cfsr%7C0%7C1675',
            '_clsk': '1q2cmsx%7C1737495976418%7C1%7C1%7Cv.clarity.ms%2Fcollect',
            'rs_ga_7D11YVFKG7': 'GS1.1.1737495976284.68.0.1737495976.0.0.0',
            '_ScCbts': '%5B%22565%3Bchrome.2%3A2%3A5%22%5D',
            'AMP_MKTG_4726fa62aa': 'JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE',
            '_cfuvid': 'qcdO3DFXhzQssbt28VSVc_skpDfjo57y94UsjRJM7AE-1737495977357-0.0.1.1-604800000',
            'AMP_4726fa62aa': 'JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJlMTIzN2NlYi0wZWUxLTQxMWYtOWYyZi01MzJiMmVkYzQ1NWQlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzM3NDk1OTc3MTEwJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTczNzQ5NTk3Nzk5NCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMTE0JTJDJTIycGFnZUNvdW50ZXIlMjIlM0ExJTdE',
            'rl_trait': 'RS_ENC_v3_eyJsYXN0X29wZW5lZF9zdGF0ZSI6IldJIiwiY3VzdG9tZXJEYXNoTGluayI6Imh0dHBzOi8vYXBpLnByaXplcGlja3MuY29tL2FkbWluL3VzZXJzL3VuZGVmaW5lZCJ9',
            'cf_clearance': 'mbKYFyM6gy86hdeTiVFUoVnlh32zFxBykO3F6jZko3c-1737496028-1.2.1.1-cKRnYP5bPJ5qYRONL64yWZxx0ePUxjixy_3DnJdb3ScJV9EFeQ7NxKJnwrROi7DCVTfjimq_Zz.Wd5zgO052UKlqf0JoD6ONNelGULwd2BbotWO4bvlZJwfm5yKbvqbydUIW0gqYz1c7GeU5T59gTM3qY2IMhdOQ92MzxIelhVVfq_fPgSdVWXE_fh1VqGIJn8ckcDPNTJxKW.Bvpu1rof3JcZyAU0OzYD5hGKYIaoLmvBSOiWIisCBRj0hh6XHBydTMTUBSlyrH6dfq9SvuiFS7hw0CupG8yb._ek2WnOY',
            '_scid_r': 'FgVk2p4lyukVH9huKCo3AgmaIFNY9S1e4xJEvw',
            'CSRF-TOKEN': 'Bl2SuiTBIjb8tMGrKFzz0I14ufMyML2KfuvpGXkdYad9lgJVd4Uh7-sWS4fTS7XrcuM2NXoY0MfiNTGzuoYMZw',
            '_prizepicks_session': 'hjxq6fWyEUpipqPQYrBr61GYIEMygJtt%2F70pa0DieA3tOroIfcjCVSXBnCZEVqQL%2BwlDFEK%2BWpaRq0DyEBOHCkU1ak%2Bqw08DWRqvncQWw1T4UHtCj1a8jCZiB0UYq196KydIwx19rGxXikdhX3FRxiDvq0cSB1u2fEWdbonIdivDVKAQGtU6KIZP7%2Bj7Jm3%2F%2F0IJktisEB3g4DoUWrNrierMUEnrYCM8l%2FT%2FAgD%2Fz3Pn7VEVtgx7IwmuDgoytBnwNzULvHBFq6HnsgkmbtKBIcSj8USjrItwIjv%2FD24etB%2BenleB50SyuRxiKwTHlEH97Q%3D%3D--ilVi631iETg3RNtZ--C9ZCYZvvlUwiOsX0X5k6ew%3D%3D',
            '_rdt_uuid': '1722642439121.a171180b-e631-46d8-8c6d-d3d49a354e68',
            'rl_session': 'RS_ENC_v3_eyJpZCI6MTczNzQ5NTk3NjI4NCwiZXhwaXJlc0F0IjoxNzM3NDk4NjE5MTg1LCJ0aW1lb3V0IjoxODAwMDAwLCJhdXRvVHJhY2siOnRydWUsInNlc3Npb25TdGFydCI6ZmFsc2V9',
            '__cf_bm': 'MUVYQsRMsZl_YTZD_Uhj_zwEK7b98wY8y_rVj.COSnU-1737497789-1.0.1.1-XAvK0gfsWlKxKfjUAnzXO3FaQanXOAl6On254cwXz3b_fqyxHtr96sZH438DyhfsMZPkCe_g0hmBXM49l3bnPA',
            '_px3': 'd26ffd65d28c6b7b0eef4cf9126f78932df12a0b447c4d723d331fdd85479cfa:/1ocqrBA5SZ+5xNVHLVZz3NM3ZNsDOVKhySVSwbKQ18IypJFdAt7rUxuRLWGf5ps2m58jWVYOokhN48kNDaVcg==:1000:pgOATQOfzFiCwrlv6YkUTM8cMKVAvMMIwTqT9TCW15rDfyoqMEmYMy69l85THSpn+NFT9t74Z9nVFk7fLx1/nAkDL0/Ps30387maPg7hoH2cUwrA8VbFBRvoFFdYIfQj75o/fi3o9UogzpuNUoWOZJ+OvHFuhBkpqZMlp89CvWZaAp/0iBnYYbb+QiotTkTzukIRhEytFXoUqSfQEcc+pZOLIgydWlwRNqsnqssx1k4=',
        },
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'if-modified-since': 'Tue, 21 Jan 2025 22:21:58 GMT',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
    )
    asd = 123

    
if __name__ == '__main__':
    asyncio.run(main())




# import requests
#
#     cookies = {
#         'ajs_anonymous_id': '0c20e023-4ac3-4d2a-aa22-72452ed28059',
#         '_fbp': 'fb.1.1722653625319.566404622364524062',
#         '_scid': '64da9e25-cae9-4b1f-bf6e-282a3702099a',
#         '__podscribe_prizepicks_referrer': '_',
#         '__podscribe_prizepicks_landing_url': 'https://www.prizepicks.com/',
#         '__podscribe_did': 'pscrb_93729ef9-6531-4397-dfb2-900057db982e',
#         'afUserId': '5e932583-c2bb-4461-98fa-1b5e1b1a26c7-p',
#         '_pxvid': '9aea1505-5143-11ef-af3c-1c7e40392ae3',
#         '__pxvid': '9b130b7a-5143-11ef-ba03-0242ac120002',
#         'intercom-device-id-qmdeaj0t': 'bfcbefbf-d1bb-4f30-b3e9-a1cbcceee5b1',
#         'intercom-id-qmdeaj0t': 'f103cbcc-a5cf-4058-87e2-cd6084dc9008',
#         '_sp_id.9177': '4472dc67-cfda-4631-b867-1ffe8e11427e.1722653625.22.1724083321.1724080125.7cebba50-8ca3-4d4e-a40d-78f33f2c98fc',
#         'ab.storage.deviceId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917': '%7B%22g%22%3A%228e0de1ba-3a8b-8ad7-d3ca-7ece02039dd6%22%2C%22c%22%3A1722457830004%2C%22l%22%3A1726714699655%7D',
#         'ab.storage.userId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917': '%7B%22g%22%3A%225f67121e-cc2c-4c3b-aca0-7f9a9ebc8f96%22%2C%22c%22%3A1722457830003%2C%22l%22%3A1726714699655%7D',
#         'ab.storage.sessionId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917': '%7B%22g%22%3A%2256cb5c53-3c38-e6d2-9c9e-45ecb1b28a22%22%2C%22e%22%3A1726716499693%2C%22c%22%3A1726714699654%2C%22l%22%3A1726714699693%7D',
#         '_tt_enable_cookie': '1',
#         '_vwo_uuid_v2': 'D87EAA71160DE47A379FAECEC3EB7A00C|22637891b01e5ec2a6540cd2f175a225',
#         '_gcl_au': '1.1.558188604.1730824779',
#         '_ttp': 'X7DD4QodZBUUH_mkQI9ifF0bdyp.tt.1',
#         'intercom-session-qmdeaj0t': '',
#         'rl_anonymous_id': 'RS_ENC_v3_IjQ0MWQwNzQzLTZhYjYtNGVjNC04NTBjLWQwMTllY2Q4NmQ3YyI%3D',
#         'rl_page_init_referrer': 'RS_ENC_v3_IiRkaXJlY3Qi',
#         'rs_ga': 'GA1.1.441d0743-6ab6-4ec4-850c-d019ecd86d7c',
#         'pxcts': '5caf9d90-cbf0-11ef-b9e7-785b214f4ee8',
#         'AF_SYNC': '1736967189581',
#         '_sctr': '1%7C1737007200000',
#         '_rdt_em': '0000000000000000000000000000000000000000000000000000000000000001',
#         '_clck': 'xtr0pf%7C2%7Cfsr%7C0%7C1675',
#         '_clsk': '1q2cmsx%7C1737495976418%7C1%7C1%7Cv.clarity.ms%2Fcollect',
#         'rs_ga_7D11YVFKG7': 'GS1.1.1737495976284.68.0.1737495976.0.0.0',
#         '_ScCbts': '%5B%22565%3Bchrome.2%3A2%3A5%22%5D',
#         'AMP_MKTG_4726fa62aa': 'JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE',
#         '_cfuvid': 'qcdO3DFXhzQssbt28VSVc_skpDfjo57y94UsjRJM7AE-1737495977357-0.0.1.1-604800000',
#         'AMP_4726fa62aa': 'JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJlMTIzN2NlYi0wZWUxLTQxMWYtOWYyZi01MzJiMmVkYzQ1NWQlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzM3NDk1OTc3MTEwJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTczNzQ5NTk3Nzk5NCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMTE0JTJDJTIycGFnZUNvdW50ZXIlMjIlM0ExJTdE',
#         'rl_trait': 'RS_ENC_v3_eyJsYXN0X29wZW5lZF9zdGF0ZSI6IldJIiwiY3VzdG9tZXJEYXNoTGluayI6Imh0dHBzOi8vYXBpLnByaXplcGlja3MuY29tL2FkbWluL3VzZXJzL3VuZGVmaW5lZCJ9',
#         'cf_clearance': 'mbKYFyM6gy86hdeTiVFUoVnlh32zFxBykO3F6jZko3c-1737496028-1.2.1.1-cKRnYP5bPJ5qYRONL64yWZxx0ePUxjixy_3DnJdb3ScJV9EFeQ7NxKJnwrROi7DCVTfjimq_Zz.Wd5zgO052UKlqf0JoD6ONNelGULwd2BbotWO4bvlZJwfm5yKbvqbydUIW0gqYz1c7GeU5T59gTM3qY2IMhdOQ92MzxIelhVVfq_fPgSdVWXE_fh1VqGIJn8ckcDPNTJxKW.Bvpu1rof3JcZyAU0OzYD5hGKYIaoLmvBSOiWIisCBRj0hh6XHBydTMTUBSlyrH6dfq9SvuiFS7hw0CupG8yb._ek2WnOY',
#         '_scid_r': 'FgVk2p4lyukVH9huKCo3AgmaIFNY9S1e4xJEvw',
#         'CSRF-TOKEN': 'Bl2SuiTBIjb8tMGrKFzz0I14ufMyML2KfuvpGXkdYad9lgJVd4Uh7-sWS4fTS7XrcuM2NXoY0MfiNTGzuoYMZw',
#         '_prizepicks_session': 'hjxq6fWyEUpipqPQYrBr61GYIEMygJtt%2F70pa0DieA3tOroIfcjCVSXBnCZEVqQL%2BwlDFEK%2BWpaRq0DyEBOHCkU1ak%2Bqw08DWRqvncQWw1T4UHtCj1a8jCZiB0UYq196KydIwx19rGxXikdhX3FRxiDvq0cSB1u2fEWdbonIdivDVKAQGtU6KIZP7%2Bj7Jm3%2F%2F0IJktisEB3g4DoUWrNrierMUEnrYCM8l%2FT%2FAgD%2Fz3Pn7VEVtgx7IwmuDgoytBnwNzULvHBFq6HnsgkmbtKBIcSj8USjrItwIjv%2FD24etB%2BenleB50SyuRxiKwTHlEH97Q%3D%3D--ilVi631iETg3RNtZ--C9ZCYZvvlUwiOsX0X5k6ew%3D%3D',
#         '_rdt_uuid': '1722642439121.a171180b-e631-46d8-8c6d-d3d49a354e68',
#         'rl_session': 'RS_ENC_v3_eyJpZCI6MTczNzQ5NTk3NjI4NCwiZXhwaXJlc0F0IjoxNzM3NDk4NjE5MTg1LCJ0aW1lb3V0IjoxODAwMDAwLCJhdXRvVHJhY2siOnRydWUsInNlc3Npb25TdGFydCI6ZmFsc2V9',
#         '__cf_bm': 'MUVYQsRMsZl_YTZD_Uhj_zwEK7b98wY8y_rVj.COSnU-1737497789-1.0.1.1-XAvK0gfsWlKxKfjUAnzXO3FaQanXOAl6On254cwXz3b_fqyxHtr96sZH438DyhfsMZPkCe_g0hmBXM49l3bnPA',
#         '_px3': 'd26ffd65d28c6b7b0eef4cf9126f78932df12a0b447c4d723d331fdd85479cfa:/1ocqrBA5SZ+5xNVHLVZz3NM3ZNsDOVKhySVSwbKQ18IypJFdAt7rUxuRLWGf5ps2m58jWVYOokhN48kNDaVcg==:1000:pgOATQOfzFiCwrlv6YkUTM8cMKVAvMMIwTqT9TCW15rDfyoqMEmYMy69l85THSpn+NFT9t74Z9nVFk7fLx1/nAkDL0/Ps30387maPg7hoH2cUwrA8VbFBRvoFFdYIfQj75o/fi3o9UogzpuNUoWOZJ+OvHFuhBkpqZMlp89CvWZaAp/0iBnYYbb+QiotTkTzukIRhEytFXoUqSfQEcc+pZOLIgydWlwRNqsnqssx1k4=',
#     }
#
#     headers = {
#         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         'accept-language': 'en-US,en;q=0.9',
#         'cache-control': 'max-age=0',
#         # 'cookie': 'ajs_anonymous_id=0c20e023-4ac3-4d2a-aa22-72452ed28059; _fbp=fb.1.1722653625319.566404622364524062; _scid=64da9e25-cae9-4b1f-bf6e-282a3702099a; __podscribe_prizepicks_referrer=_; __podscribe_prizepicks_landing_url=https://www.prizepicks.com/; __podscribe_did=pscrb_93729ef9-6531-4397-dfb2-900057db982e; afUserId=5e932583-c2bb-4461-98fa-1b5e1b1a26c7-p; _pxvid=9aea1505-5143-11ef-af3c-1c7e40392ae3; __pxvid=9b130b7a-5143-11ef-ba03-0242ac120002; intercom-device-id-qmdeaj0t=bfcbefbf-d1bb-4f30-b3e9-a1cbcceee5b1; intercom-id-qmdeaj0t=f103cbcc-a5cf-4058-87e2-cd6084dc9008; _sp_id.9177=4472dc67-cfda-4631-b867-1ffe8e11427e.1722653625.22.1724083321.1724080125.7cebba50-8ca3-4d4e-a40d-78f33f2c98fc; ab.storage.deviceId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917=%7B%22g%22%3A%228e0de1ba-3a8b-8ad7-d3ca-7ece02039dd6%22%2C%22c%22%3A1722457830004%2C%22l%22%3A1726714699655%7D; ab.storage.userId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917=%7B%22g%22%3A%225f67121e-cc2c-4c3b-aca0-7f9a9ebc8f96%22%2C%22c%22%3A1722457830003%2C%22l%22%3A1726714699655%7D; ab.storage.sessionId.c7cca5c1-d2b5-4a33-9307-cfe8427a0917=%7B%22g%22%3A%2256cb5c53-3c38-e6d2-9c9e-45ecb1b28a22%22%2C%22e%22%3A1726716499693%2C%22c%22%3A1726714699654%2C%22l%22%3A1726714699693%7D; _tt_enable_cookie=1; _vwo_uuid_v2=D87EAA71160DE47A379FAECEC3EB7A00C|22637891b01e5ec2a6540cd2f175a225; _gcl_au=1.1.558188604.1730824779; _ttp=X7DD4QodZBUUH_mkQI9ifF0bdyp.tt.1; intercom-session-qmdeaj0t=; rl_anonymous_id=RS_ENC_v3_IjQ0MWQwNzQzLTZhYjYtNGVjNC04NTBjLWQwMTllY2Q4NmQ3YyI%3D; rl_page_init_referrer=RS_ENC_v3_IiRkaXJlY3Qi; rs_ga=GA1.1.441d0743-6ab6-4ec4-850c-d019ecd86d7c; pxcts=5caf9d90-cbf0-11ef-b9e7-785b214f4ee8; AF_SYNC=1736967189581; _sctr=1%7C1737007200000; _rdt_em=0000000000000000000000000000000000000000000000000000000000000001; _clck=xtr0pf%7C2%7Cfsr%7C0%7C1675; _clsk=1q2cmsx%7C1737495976418%7C1%7C1%7Cv.clarity.ms%2Fcollect; rs_ga_7D11YVFKG7=GS1.1.1737495976284.68.0.1737495976.0.0.0; _ScCbts=%5B%22565%3Bchrome.2%3A2%3A5%22%5D; AMP_MKTG_4726fa62aa=JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE; _cfuvid=qcdO3DFXhzQssbt28VSVc_skpDfjo57y94UsjRJM7AE-1737495977357-0.0.1.1-604800000; AMP_4726fa62aa=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJlMTIzN2NlYi0wZWUxLTQxMWYtOWYyZi01MzJiMmVkYzQ1NWQlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzM3NDk1OTc3MTEwJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTczNzQ5NTk3Nzk5NCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMTE0JTJDJTIycGFnZUNvdW50ZXIlMjIlM0ExJTdE; rl_trait=RS_ENC_v3_eyJsYXN0X29wZW5lZF9zdGF0ZSI6IldJIiwiY3VzdG9tZXJEYXNoTGluayI6Imh0dHBzOi8vYXBpLnByaXplcGlja3MuY29tL2FkbWluL3VzZXJzL3VuZGVmaW5lZCJ9; cf_clearance=mbKYFyM6gy86hdeTiVFUoVnlh32zFxBykO3F6jZko3c-1737496028-1.2.1.1-cKRnYP5bPJ5qYRONL64yWZxx0ePUxjixy_3DnJdb3ScJV9EFeQ7NxKJnwrROi7DCVTfjimq_Zz.Wd5zgO052UKlqf0JoD6ONNelGULwd2BbotWO4bvlZJwfm5yKbvqbydUIW0gqYz1c7GeU5T59gTM3qY2IMhdOQ92MzxIelhVVfq_fPgSdVWXE_fh1VqGIJn8ckcDPNTJxKW.Bvpu1rof3JcZyAU0OzYD5hGKYIaoLmvBSOiWIisCBRj0hh6XHBydTMTUBSlyrH6dfq9SvuiFS7hw0CupG8yb._ek2WnOY; _scid_r=FgVk2p4lyukVH9huKCo3AgmaIFNY9S1e4xJEvw; CSRF-TOKEN=Bl2SuiTBIjb8tMGrKFzz0I14ufMyML2KfuvpGXkdYad9lgJVd4Uh7-sWS4fTS7XrcuM2NXoY0MfiNTGzuoYMZw; _prizepicks_session=hjxq6fWyEUpipqPQYrBr61GYIEMygJtt%2F70pa0DieA3tOroIfcjCVSXBnCZEVqQL%2BwlDFEK%2BWpaRq0DyEBOHCkU1ak%2Bqw08DWRqvncQWw1T4UHtCj1a8jCZiB0UYq196KydIwx19rGxXikdhX3FRxiDvq0cSB1u2fEWdbonIdivDVKAQGtU6KIZP7%2Bj7Jm3%2F%2F0IJktisEB3g4DoUWrNrierMUEnrYCM8l%2FT%2FAgD%2Fz3Pn7VEVtgx7IwmuDgoytBnwNzULvHBFq6HnsgkmbtKBIcSj8USjrItwIjv%2FD24etB%2BenleB50SyuRxiKwTHlEH97Q%3D%3D--ilVi631iETg3RNtZ--C9ZCYZvvlUwiOsX0X5k6ew%3D%3D; _rdt_uuid=1722642439121.a171180b-e631-46d8-8c6d-d3d49a354e68; rl_session=RS_ENC_v3_eyJpZCI6MTczNzQ5NTk3NjI4NCwiZXhwaXJlc0F0IjoxNzM3NDk4NjE5MTg1LCJ0aW1lb3V0IjoxODAwMDAwLCJhdXRvVHJhY2siOnRydWUsInNlc3Npb25TdGFydCI6ZmFsc2V9; __cf_bm=MUVYQsRMsZl_YTZD_Uhj_zwEK7b98wY8y_rVj.COSnU-1737497789-1.0.1.1-XAvK0gfsWlKxKfjUAnzXO3FaQanXOAl6On254cwXz3b_fqyxHtr96sZH438DyhfsMZPkCe_g0hmBXM49l3bnPA; _px3=d26ffd65d28c6b7b0eef4cf9126f78932df12a0b447c4d723d331fdd85479cfa:/1ocqrBA5SZ+5xNVHLVZz3NM3ZNsDOVKhySVSwbKQ18IypJFdAt7rUxuRLWGf5ps2m58jWVYOokhN48kNDaVcg==:1000:pgOATQOfzFiCwrlv6YkUTM8cMKVAvMMIwTqT9TCW15rDfyoqMEmYMy69l85THSpn+NFT9t74Z9nVFk7fLx1/nAkDL0/Ps30387maPg7hoH2cUwrA8VbFBRvoFFdYIfQj75o/fi3o9UogzpuNUoWOZJ+OvHFuhBkpqZMlp89CvWZaAp/0iBnYYbb+QiotTkTzukIRhEytFXoUqSfQEcc+pZOLIgydWlwRNqsnqssx1k4=',
#         'if-modified-since': 'Tue, 21 Jan 2025 22:21:58 GMT',
#         'priority': 'u=0, i',
#         'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"macOS"',
#         'sec-fetch-dest': 'document',
#         'sec-fetch-mode': 'navigate',
#         'sec-fetch-site': 'none',
#         'sec-fetch-user': '?1',
#         'upgrade-insecure-requests': '1',
#         'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
#     }
#
#     params = {
#         'league_id': '9',
#         'per_page': '250',
#         'single_stat': 'true',
#         'in_game': 'true',
#         'state_code': 'WI',
#         'game_mode': 'pickem',
#     }
#
#     response = requests.get('https://api.prizepicks.com/projections', params=params, cookies=cookies, headers=headers)
#     asd = 123