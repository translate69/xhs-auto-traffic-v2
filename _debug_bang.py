import sys
for mod in list(sys.modules.keys()):
    if 'filter' in mod or 'classifier' in mod:
        del sys.modules[mod]
sys.path.insert(0, '.')
from filter.filter_service import FilterService, has_signal, ASK_SIGNALS
from core.note_detail import NoteDetail

content = '''避开五一节假日高峰 带娃出行 人真的不多
金町湾去啦 二马路去啦 杯杯鲜喝啦 吉祥大排档也去啦
住的金町湾希尔顿 网上看到有差评 也有好评 就我而言还是不错的 前台帮我们免费升级了海景房 还送了曲奇饼干 只是早餐显得略微单调 住了2晚 退房的时候又送了伴手礼
对于重庆人来说 吃的真的不太合我的胃口 杯杯鲜倒还不错 来了2天 已经干3杯了
跟着刘雨鑫打卡了吉祥大排档 价格非常实惠的 只是味道对我重庆胃来说有点寡淡 没我想象中的美味'''

note = NoteDetail(title='??汕尾', content=content, url='https://www.xiaohongshu.com/explore/69fdadf8', xsec_token='test', author='是可爱的我呀', published_at='2026-05-03')
svc = FilterService()
result = svc.filter_one(note)
print(f'passed={result.passed}, reasons={result.reasons}')
print(f'ASK_SIGNALS contains bang: {"帮我" in ASK_SIGNALS}')
print(f'has_signal帮我: {has_signal(content, ["帮我"])}')
