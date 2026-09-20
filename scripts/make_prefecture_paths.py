#!/usr/bin/env python3
"""jpn-atlas の TopoJSON から、都道府県ごとの SVG パスを つくる。

apps/japan/index.html に 埋めこんでいる 地図データの もとになった スクリプト。
出典: 国土地理院「地球地図日本」2016 を もとに した jpn-atlas (BSD-3-Clause)。
くわしくは apps/japan/MAP_DATA_LICENSE.txt を 見てください。

つかいかた:
    npm i jpn-atlas          # node_modules/jpn-atlas/japan/japan.json が 必要
    python3 scripts/make_prefecture_paths.py
  → scripts/prefecture_paths.json（アプリに 埋めこむ 地図データ）

アプリの HTML には この JSON が すでに 入っているので、
地図を 作りなおしたい ときだけ 実行する。
"""
import json
import math
import sys

SRC = 'node_modules/jpn-atlas/japan/japan.json'
OUT = 'scripts/prefecture_paths.json'

EPS = 0.45          # 単純化（ダグラス・ポイカー）の しきい値
MIN_AREA = 2.5      # これより 小さい 島は のぞく（座標の 2乗）
KEEP_BIGGEST = 1    # 面積が 小さくても 各県の いちばん大きい 輪は のこす


def load_arcs(topo):
    tr = topo['transform']
    sx, sy = tr['scale']
    tx, ty = tr['translate']
    arcs = []
    for arc in topo['arcs']:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def ring_points(arcs, idxs):
    pts = []
    for i in idxs:
        a = arcs[~i][::-1] if i < 0 else arcs[i]
        pts.extend(a if not pts else a[1:])
    return pts


def rings_of(geom, arcs):
    """外側の 輪だけ あつめる（穴は 使わない）"""
    out = []
    if geom['type'] == 'Polygon':
        polys = [geom['arcs']]
    else:
        polys = geom['arcs']
    for poly in polys:
        if not poly:
            continue
        out.append(ring_points(arcs, poly[0]))   # poly[0] = 外周
    return out


def area(ring):
    s = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def simplify(pts, eps):
    """ダグラス・ポイカー（再帰なし）"""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        best, bestd = -1, 0.0
        for i in range(a + 1, b):
            px, py = pts[i]
            if norm < 1e-9:
                # 輪の さいしょと さいごは 同じ点。基準線が つくれないので
                # 「始点から いちばん 遠い点」で 2つに わける
                d = math.hypot(px - ax, py - ay)
            else:
                d = abs(dy * (px - ax) - dx * (py - ay)) / norm
            if d > bestd:
                best, bestd = i, d
        if bestd > eps and best > 0:
            keep[best] = True
            stack.append((a, best))
            stack.append((best, b))
    return [p for p, k in zip(pts, keep) if k]


def centroid(ring):
    cx = cy = a = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        cr = x1 * y2 - x2 * y1
        a += cr
        cx += (x1 + x2) * cr
        cy += (y1 + y2) * cr
    if abs(a) < 1e-9:
        return ring[0]
    a *= 0.5
    return (cx / (6 * a), cy / (6 * a))


def main():
    topo = json.load(open(SRC))
    arcs = load_arcs(topo)
    prefs = topo['objects']['prefectures']['geometries']
    assert len(prefs) == 47, len(prefs)

    result = []
    for i, geom in enumerate(prefs):
        rings = rings_of(geom, arcs)
        rings.sort(key=area, reverse=True)
        kept = [r for r in rings if area(r) >= MIN_AREA] or rings[:KEEP_BIGGEST]
        result.append({'code': i + 1, 'rings': kept, 'dropped': len(rings) - len(kept)})

    # とても 遠（とお）くの 島は のぞく（東京の 小笠原、鹿児島の 奄美 など）。
    # 地図が すかすかに ならないように、いちばん 大きい 島の 近くだけ のこす。
    FAR = 45
    for pref in result:
        biggest = max(pref['rings'], key=area)
        bc = centroid(biggest)
        near = [r for r in pref['rings'] if math.dist(centroid(r), bc) < FAR]
        pref['far_dropped'] = len(pref['rings']) - len(near)
        pref['rings'] = near

    # 単純化
    total_pts_before = total_pts_after = 0
    for pref in result:
        new_rings = []
        for r in pref['rings']:
            total_pts_before += len(r)
            s = simplify(r, EPS)
            if len(s) >= 4:
                total_pts_after += len(s)
                new_rings.append(s)
        pref['rings'] = new_rings or [simplify(max(pref['rings'], key=area), EPS / 3)]

    # 沖縄を 左下の わくの 中へ 移動
    oki = result[46]
    ocx, ocy = centroid(max(oki['rings'], key=area))
    OKI_TARGET = (86, 470)
    ox, oy = OKI_TARGET[0] - ocx, OKI_TARGET[1] - ocy
    oki['rings'] = [[(x + ox, y + oy) for x, y in r] for r in oki['rings']]
    oki['inset'] = True

    # 全体を viewBox に おさめる
    xs = [x for p in result for r in p['rings'] for x, y in r]
    ys = [y for p in result for r in p['rings'] for x, y in r]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    pad = 20
    W, H = maxx - minx + pad * 2, maxy - miny + pad * 2

    out = {'view': [round(W, 1), round(H, 1)], 'prefectures': [], 'inset_box': None}
    for pref in result:
        paths = []
        for r in pref['rings']:
            pts = [(round(x - minx + pad, 1), round(y - miny + pad, 1)) for x, y in r]
            d = 'M' + ' L'.join(f'{x},{y}' for x, y in pts) + ' Z'
            paths.append(d)
        big = max(pref['rings'], key=area)
        cx, cy = centroid(big)
        pxs = [x - minx + pad for r in pref['rings'] for x, y in r]
        pys = [y - miny + pad for r in pref['rings'] for x, y in r]
        out['prefectures'].append({
            'code': pref['code'],
            'path': ' '.join(paths),
            'label': [round(cx - minx + pad, 1), round(cy - miny + pad, 1)],
            'islands': len(paths),
            # タップしやすさの 判断に つかう 大きさ
            'size': round(max(max(pxs) - min(pxs), max(pys) - min(pys)), 1)
        })

    # 沖縄の わく
    oxs = [x for r in result[46]['rings'] for x, y in r]
    oys = [y for r in result[46]['rings'] for x, y in r]
    out['inset_box'] = [round(min(oxs) - minx + pad - 10, 1), round(min(oys) - miny + pad - 10, 1),
                        round(max(oxs) - min(oxs) + 20, 1), round(max(oys) - min(oys) + 20, 1)]

    json.dump(out, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
    size = len(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    print(f'viewBox: {out["view"]}')
    print(f'点の数: {total_pts_before} -> {total_pts_after}')
    print(f'出力: {OUT} ({size / 1024:.1f} KB)')
    print('島の数:', sum(p['islands'] for p in out['prefectures']))
    print('沖縄のわく:', out['inset_box'])


if __name__ == '__main__':
    main()
