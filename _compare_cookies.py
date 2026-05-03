import json, sys
sys.path.insert(0, '.')

# Chrome 完整 cookie 字符串（从用户复制）
chrome_cookie_str = "abRequestId=a8f88da1-057d-5c73-b0ba-bc39fa651e56; a1=19cf4b919fcdl05vge657pfskagn3ab8pv5ilxr4x50000425850; webId=997b31e05787f2a2b470f596a7213675; gid=yjSi4Djq24UDyjSi4DjyjhCFiSf182hkdK2W24CUiMT0k328Iq0DY18884J2Y288yqSq8iyY; customerClientId=260866825254630; x-user-id-creator.xiaohongshu.com=5893748050c4b42b98f652d8; access-token-creator.xiaohongshu.com=customer.creator.AT-68c517624463194275659778jzarpspuqslcjwgw; galaxy_creator_session_id=ACBOZ3pf0Py9gYTJFBQKc2ILAlnNTYm7Jv2c; galaxy.creator.beaker.session.id=1775208673076032936353; ets=1777037693976; web_session=04006976927b841530974bc6c43b4b5d49191d; id_token=VjEAAE3uB0HQBCbx7YhlIyDIZ9ovJUBDKl72fT+FhJYgWwtvLyvE3hZwtXirk8puhQig/OLtkHyEg6v7yuH+JE0hLPqtJQahkMkRtbqsjwqj7eDmdFolPjx9zYmBQGjmHCdQba40; webBuild=6.7.6; xsecappid=xhs-pc-web; websectiga=3633fe24d49c7dd0eb923edc8205740f10fdb18b25d424d2a2322c6196d2a4ad; sec_poison_id=b0070bc7-32c4-4f26-ac90-31a1096c139c; unread={%22ub%22:%2269f1ada70000000035029e95%22%2C%22ue%22:%2269f1b277000000003501ebfc%22%2C%22uc%22:28}; loadts=1777445920552"

# 从字符串解析出 cookie dict
chrome_cookies = {}
for part in chrome_cookie_str.split("; "):
    if "=" in part:
        name, value = part.split("=", 1)
        chrome_cookies[name] = value

# 读取文件里的 cookie
file_cookies = json.load(open('xhs_cookies.json'))
file_cookie_names = {c['name'] for c in file_cookies}

print("=== Chrome 有但 xhs_cookies.json 没有的 cookie ===")
for name, value in chrome_cookies.items():
    if name not in file_cookie_names:
        print(f"  {name} = {value[:40]}...")

print("\n=== 值有差异的 cookie ===")
for c in file_cookies:
    name = c['name']
    if name in chrome_cookies:
        if c['value'] != chrome_cookies[name]:
            print(f"  {name}:")
            print(f"    文件: {c['value'][:50]}...")
            print(f"    Chrome: {chrome_cookies[name][:50]}...")

print(f"\n=== Chrome 总数: {len(chrome_cookies)} | 文件总数: {len(file_cookies)} ===")
print("\n=== 完整 Chrome cookie list ===")
for name, value in chrome_cookies.items():
    print(f"  {name}: {value}")