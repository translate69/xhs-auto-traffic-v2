# -*- coding: utf-8 -*-
"""深入分析两篇笔记的 filter 判定原因"""
import json, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from filter.filter_service import FilterService, FilterResult
from core.note_detail import NoteDetail
from core.search_collector import FeedNote
import filter.filter_service as fs_module

with open('data/collected/runs/2026-05-09_汕尾美食.jsonl', encoding='utf-8') as f:
    lines = f.readlines()

target_ids = ['69f76a0d000000002202b546', '69fe050a000000002003b0c8']
notes = [json.loads(l) for l in lines if any(tid in l for tid in target_ids)]

for note_data in notes:
    nid = re.search(r'search_result/([a-f0-9]+)', note_data['url']).group(1)
    print("=" * 60)
    print(f"note_id: {nid}")
    print(f"title: {note_data.get('title', '')}")
    print(f"content:\n{note_data.get('content', '')}")
    print(f"tags: {note_data.get('tags', [])}")

    feed = FeedNote()
    feed.url = note_data.get('url', '')
    feed.xsec_token = note_data.get('xsec_token', '')
    feed.author = note_data.get('author', '')
    feed.time_text = note_data.get('time_text', '')
    feed.title = note_data.get('title', '')

    nd = NoteDetail()
    nd.merge_from_feed(feed)
    nd.content = note_data.get('content', '')
    nd.tags = note_data.get('tags', [])
    nd.images = note_data.get('images', [])
    nd.published_at = note_data.get('published_at', '')

    # Call filter_one_impl directly to get debug info
    result = fs_module.FilterService().filter_one_impl(nd, skip_time_check=False)

    print(f"\n--- FilterDebug ---")
    print(f"  passed: {result.passed}")
    print(f"  reasons: {result.reasons}")
    print(f"  note_type: {result.note_type}")
    print()