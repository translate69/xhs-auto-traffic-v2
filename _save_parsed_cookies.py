# -*- coding: utf-8 -*-
import json

raw = "abRequestId=a8f88da1-057d-5c73-b0ba-bc39fa651e56; a1=19cf4b919fcdl05vge657pfskagn3ab8pv5ilxr4x50000425850; webId=997b31e05787f2a2b470f596a7213675; gid=yjSi4Djq24UDyjSi4DjyjhCFiSf182hkdK2W24CUiMT0k328Iq0DY18884J2Y288yqSq8iyY; customerClientId=260866825254630; x-user-id-creator.xiaohongshu.com=5893748050c4b42b98f652d8; access-token-creator.xiaohongshu.com=customer.creator.AT-68c517624463194275659778jzarpspuqslcjwgw; galaxy_creator_session_id=ACBOZ3pf0Py9gYTJFBQKc2ILAlnNTYm7Jv2c; galaxy.creator.beaker.session.id=1775208673076032936353; ets=1777037693976; xsecappid=xhs-pc-web; webBuild=6.7.6; loadts=1777438146556; acw_tc=0a0b147517774381468061918e4b3e825a3d15e952bf42233a474f81e9ed2b; websectiga=2a3d3ea002e7d92b5c9743590ebd24010cf3710ff3af8029153751e41a6af4a3; sec_poison_id=5c9288ec-7026-4386-943f-bb76b2b17540; web_session=04006976927b841530974bc6c43b4b5d49191d; id_token=VjEAAE3uB0HQBCbx7YhlIyDIZ9ovJUBDKl72fT+FhJYgWwtvLyvE3hZwtXirk8puhQig/OLtkHyEg6v7yuH+JE0hLPqtJQahkMkRtbqsjwqj7eDmdFolPjx9zYmBQGjmHCdQba40; unread={%22ub%22:%2269f186bb000000002202bac3%22%2C%22ue%22:%2269ece9460000000038037fcd%22%2C%22uc%22:21}"

cookies = []
for part in raw.split(";"):
    part = part.strip()
    if "=" in part:
        name, value = part.split("=", 1)
        cookies.append({
            "domain": "xiaohongshu.com",   # 无前导点
            "name": name.strip(),
            "value": value.strip(),
            "path": "/",
            "secure": True,
            "expires": -1,
            "httpOnly": False
        })

with open("xhs_cookies.json", "w", encoding="utf-8") as f:
    json.dump(cookies, f, ensure_ascii=False, indent=2)

print(f"已保存 {len(cookies)} 条 cookie")
print("web_session 确认:", any(x["name"] == "web_session" for x in cookies))
