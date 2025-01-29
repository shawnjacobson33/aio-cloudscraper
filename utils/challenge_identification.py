import re

import aiohttp


class ChallengeIdentification:
    
    def __init__(self, resp: aiohttp.ClientResponse, resp_text: str):
        self.resp = resp
        self.resp_text = resp_text
        
    def is_new_iuam_challenge(self) -> bool:
        try:
            return (
                self.is_iuam_challenge()
                and re.search(
                    r'''cpo.src\s*=\s*['"]/cdn-cgi/challenge-platform/\S+orchestrate/jsch/v1''',
                    self.resp_text,
                    re.M | re.S
                )
            )
        
        except AttributeError:
            pass
    
        return False
    
    def is_iuam_challenge(self) -> bool:
        try:
            return (
                self.resp.headers.get('Server', '').startswith('cloudflare')
                and self.resp.status in [429, 503]
                and re.search(r'/cdn-cgi/images/trace/jsch/', self.resp_text, re.M | re.S)
                and re.search(
            r'''<form .*?="challenge-form" action="/\S+__cf_chl_f_tk=''',
                    self.resp_text,
                    re.M | re.S
                )
            )
        
        except AttributeError:
            pass
    
        return False
    
    def is_new_captcha_challenge(self) -> bool:
        try:
            return (
                self.is_captcha_challenge()
                and re.search(
             r'''cpo.src\s*=\s*['"]/cdn-cgi/challenge-platform/\S+orchestrate/(captcha|managed)/v1''',
                    self.resp_text,
                    re.M | re.S
                )
            )
    
        except AttributeError:
            pass
    
        return False
    
    def is_captcha_challenge(self) -> bool:
        try:
            return (
                self.resp.headers.get('Server', '').startswith('cloudflare')
                and self.resp.status == 403
                and re.search(
                    r'<span class="cf-error-code">1020</span>',
                    self.resp_text,
                    re.M | re.DOTALL
                )
                and re.search(r'/cdn-cgi/images/trace/(captcha|managed)/', self.resp_text, re.M | re.S)
                and re.search(
             r'''<form .*?="challenge-form" action="/\S+__cf_chl_f_tk=''',
                    self.resp_text,
                    re.M | re.S
                )
            )
    
        except AttributeError:
            pass
    
        return False