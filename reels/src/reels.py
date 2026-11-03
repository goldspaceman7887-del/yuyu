"""Timelines for the three Yutoriba Bible reels.

Sources (reels/sources):
  T  train_straps_sunset.jpg  still, 1920x1080 - hand straps, sunset through the train window
  C  cafe_dusk_window.mp4     1280x704 24fps 5.04 s - cafe counter, grinder, city at dusk
  M  cafe_man_book.mp4        1280x704 24fps 5.04 s - young man at the window, coffee, a book appears
  P  train_commuters.mp4      1280x704 24fps 5.04 s - commuters on their phones, golden light

Each shot: src, dur (s), t0 (source start s), speed, cx0/cx1 (crop centre x in source px),
z0/z1 (zoom, 1.0 = full source height), cy (crop centre y, optional).
Text blocks: t (s from reel start), out (s, or None = hold), top (px), lines [(text, size)],
kind: "line" | "quote" | "close" | "brand".
"""

XF = 0.7  # crossfade between shots

REELS = {
    # ---------------------------------------------------------------- 1. reading / discovery
    "01_kotoba": dict(
        title="ことばを、ひらく",
        shots=[
            dict(src="P", dur=3.9, t0=0.0, speed=0.85, cx0=520, cx1=700, z0=1.0, z1=1.05),
            dict(src="T", dur=3.9, cx0=930, cx1=830, z0=1.0, z1=1.08),
            dict(src="C", dur=3.9, t0=0.0, speed=0.85, cx0=740, cx1=860, z0=1.05, z1=1.0),
            dict(src="M", dur=7.4, t0=0.0, speed=0.68, cx0=760, cx1=372, z0=1.0, z1=1.0),
        ],
        text=[
            dict(t=0.35, out=3.15, top=1180, kind="line",
                 lines=[("毎日、", 54), ("たくさんの言葉を読んでいる。", 54)]),
            dict(t=3.65, out=6.35, top=1180, kind="line",
                 lines=[("でも、心に残る言葉は", 54), ("いくつあるだろう。", 54)]),
            dict(t=6.85, out=9.5, top=520, kind="line",
                 lines=[("何千年も、", 54), ("読み継がれてきた本がある。", 54)]),
            dict(t=10.15, out=13.2, top=470, kind="quote",
                 lines=[("「あなたのみことばは", 54), ("私の足のともしび", 54), ("私の道の光です。」", 54),
                        ("詩篇 119:105", 32)]),
            dict(t=13.55, out=None, top=400, kind="close",
                 lines=[("聖書を、", 58), ("もう少し読んでみませんか？", 58)]),
            dict(t=14.75, out=None, top=670, kind="brand",
                 lines=[("ゆとりば", 104), ("ゆっくり考える場所。", 34)]),
        ],
        caption="""毎日たくさんの言葉を読んでいるけれど、
心に残る言葉はいくつあるだろう。

何千年も読み継がれてきた一冊、聖書。
「あなたのみことばは私の足のともしび 私の道の光です。」（詩篇119:105）

もう少し、読んでみませんか？
コメントに「📖」と送ってくれたら、はじめての人向けの読み方をお届けします。

#ゆとりば #聖書 #聖書のことば #ひとやすみ #カフェ時間 #通勤時間 #読書 #こころの余白""",
    ),
    # ---------------------------------------------------------------- 2. more than life now
    "02_sonosaki": dict(
        title="いまの、その先",
        shots=[
            dict(src="C", dur=4.0, t0=0.0, speed=0.85, cx0=800, cx1=830, z0=1.0, z1=1.07),
            dict(src="M", dur=4.0, t0=0.0, speed=0.85, cx0=780, cx1=720, z0=1.0, z1=1.04),
            dict(src="P", dur=4.0, t0=0.8, speed=0.85, cx0=760, cx1=730, z0=1.06, z1=1.0),
            dict(src="T", dur=7.2, cx0=1000, cx1=1600, z0=1.0, z1=1.06),
        ],
        text=[
            dict(t=0.35, out=3.25, top=470, kind="line",
                 lines=[("今日も、", 54), ("一日が終わっていく。", 54)]),
            dict(t=3.75, out=6.55, top=1180, kind="line",
                 lines=[("明日のこと。来年のこと。", 54), ("その、もっと先のこと。", 54)]),
            dict(t=7.05, out=9.8, top=1180, kind="line",
                 lines=[("「いま」だけで、", 54), ("人生は終わるのだろうか。", 54)]),
            dict(t=10.3, out=13.15, top=470, kind="quote",
                 lines=[("「神はまた、", 56), ("人の心に永遠を", 56), ("与えられた。」", 56),
                        ("伝道者の書 3:11", 32)]),
            dict(t=13.5, out=None, top=400, kind="close",
                 lines=[("その答えを、", 58), ("聖書の中に探してみませんか？", 56)]),
            dict(t=14.7, out=None, top=670, kind="brand",
                 lines=[("ゆとりば", 104), ("ゆっくり考える場所。", 34)]),
        ],
        caption="""今日も一日が終わっていく。
明日のこと、来年のこと、そのもっと先のこと。

「いま」だけで、人生は終わるのだろうか。

「神はまた、人の心に永遠を与えられた。」（伝道者の書3:11）

その答えを、聖書の中に探してみませんか？
気になったら、保存して夜にもう一度。

#ゆとりば #聖書 #聖書のことば #人生について #夕暮れ #通勤電車 #こころの余白 #考える時間""",
    ),
    # ---------------------------------------------------------------- 3. purpose in a big city
    "03_konomachi": dict(
        title="この街で",
        shots=[
            dict(src="T", dur=3.9, cx0=1620, cx1=1520, z0=1.0, z1=1.08),
            dict(src="P", dur=4.0, t0=0.3, speed=0.85, cx0=470, cx1=740, z0=1.0, z1=1.03),
            dict(src="M", dur=4.0, t0=0.0, speed=0.85, cx0=760, cx1=760, z0=1.06, z1=1.0),
            dict(src="C", dur=7.4, t0=0.0, speed=0.68, cx0=760, cx1=860, z0=1.0, z1=1.05),
        ],
        text=[
            dict(t=0.35, out=3.15, top=1180, kind="line",
                 lines=[("この街には、", 54), ("何百万もの人が暮らしている。", 52)]),
            dict(t=3.6, out=6.45, top=1180, kind="line",
                 lines=[("なのに、ときどき", 54), ("ひとりぼっちだと感じる。", 54)]),
            dict(t=6.95, out=9.7, top=1180, kind="line",
                 lines=[("自分は、何のために", 54), ("ここにいるんだろう。", 54)]),
            dict(t=10.2, out=13.25, top=440, kind="quote",
                 lines=[("「わたしの目には、", 54), ("あなたは高価で尊い。", 54), ("わたしはあなたを愛している。」", 50),
                        ("イザヤ書 43:4", 32)]),
            dict(t=13.6, out=None, top=400, kind="close",
                 lines=[("あなたへのことばを、", 58), ("聖書で読んでみませんか？", 58)]),
            dict(t=14.8, out=None, top=670, kind="brand",
                 lines=[("ゆとりば", 104), ("ゆっくり考える場所。", 34)]),
        ],
        caption="""この街には何百万もの人が暮らしているのに、
ときどき、ひとりぼっちだと感じる。
自分は、何のためにここにいるんだろう。

「わたしの目には、あなたは高価で尊い。わたしはあなたを愛している。」（イザヤ書43:4）

あなたへのことばを、聖書で読んでみませんか？
同じように感じている人に、そっとシェアしてください。

#ゆとりば #聖書 #聖書のことば #東京 #都会暮らし #生きる意味 #ひとりの時間 #こころの余白""",
    ),
}
