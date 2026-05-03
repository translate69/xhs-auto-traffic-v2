import json

cookies = json.load(open('xhs_cookies.json'))

# 从 Chrome DevTools 拿的真实 domain 映射
# v1 的格式：cookie 发到哪个域名，就用哪个 domain
domain_map = {
    # 精确域名
    "xiaohongshu.com": ".xiaohongshu.com",  # 通配所有子域名
}

fixed = []
for c in cookies:
    name = c['name']
    old_domain = c.get('domain', '')
    
    # 特殊处理子域名专属 cookie
    if name == 'acw_tc':
        # acw_tc 在 v1 里是按子域名分的，但 .xiaohongshu.com 也能覆盖
        new_domain = ".xiaohongshu.com"
    elif name.startswith('x-user-id-creator') or name.startswith('access-token-creator') or name.startswith('galaxy_creator') or name.startswith('galaxy.creator'):
        # creator 相关域名的 cookie
        new_domain = ".xiaohongshu.com"
    else:
        # 普通 cookie 用 .xiaohongshu.com 覆盖所有子域名
        new_domain = ".xiaohongshu.com"
    
    if old_domain != new_domain:
        print(f"  {name}: '{old_domain}' -> '{new_domain}'")
    else:
        print(f"  {name}: keep '{old_domain}'")
    
    c['domain'] = new_domain
    fixed.append(c)

# 保存
with open('xhs_cookies.json', 'w', encoding='utf-8') as f:
    json.dump(fixed, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(fixed)} cookies with updated domains")
