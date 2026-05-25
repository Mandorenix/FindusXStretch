from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontDatabase,
    QFontMetricsF,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)


ICON_SIZE = 1024
OUT_DIR = Path("assets/icon_variants")
WINDOWS_FONT_PATHS = (
    Path(r"C:\Windows\Fonts\segoeuib.ttf"),
    Path(r"C:\Windows\Fonts\segoeui.ttf"),
)
FONT_FAMILY: str | None = None


@dataclass(frozen=True)
class Variant:
    slug: str
    label: str
    ring_dark: QColor
    ring_light: QColor
    badge_inner: QColor
    accent: QColor
    text_fill: QColor
    text_shadow: QColor
    ribbon_fill: QColor
    ribbon_outline: QColor
    waveform: QColor
    monochrome: bool = False
    exact_badge: bool = False
    draw_orbits: bool = True
    compact_ribbon: bool = False
    tiny_ribbon: bool = False
    exact_level: int = 0


VARIANTS = [
    Variant(
        slug="findus_cat_classic",
        label="Classic Silver",
        ring_dark=QColor("#141414"),
        ring_light=QColor("#9a9a9a"),
        badge_inner=QColor("#585858"),
        accent=QColor("#d7d7d7"),
        text_fill=QColor("#f6f6f6"),
        text_shadow=QColor(0, 0, 0, 180),
        ribbon_fill=QColor(25, 25, 25, 210),
        ribbon_outline=QColor("#bdbdbd"),
        waveform=QColor(255, 255, 255, 55),
        monochrome=True,
    ),
    Variant(
        slug="findus_cat_midnight",
        label="Midnight Neon",
        ring_dark=QColor("#051219"),
        ring_light=QColor("#23e6cf"),
        badge_inner=QColor("#12313c"),
        accent=QColor("#d9fffb"),
        text_fill=QColor("#dbfff7"),
        text_shadow=QColor(0, 0, 0, 170),
        ribbon_fill=QColor(5, 18, 25, 220),
        ribbon_outline=QColor("#23e6cf"),
        waveform=QColor(35, 230, 207, 65),
    ),
    Variant(
        slug="findus_cat_stamp",
        label="Black Stamp",
        ring_dark=QColor("#111111"),
        ring_light=QColor("#cabda6"),
        badge_inner=QColor("#403a30"),
        accent=QColor("#f1e7d6"),
        text_fill=QColor("#fff8ec"),
        text_shadow=QColor(0, 0, 0, 155),
        ribbon_fill=QColor(17, 17, 17, 220),
        ribbon_outline=QColor("#cabda6"),
        waveform=QColor(241, 231, 214, 45),
        monochrome=True,
    ),
    Variant(
        slug="findus_cat_orbit",
        label="Orbit Wave",
        ring_dark=QColor("#1c1634"),
        ring_light=QColor("#f0a73f"),
        badge_inner=QColor("#372a5f"),
        accent=QColor("#fff1d5"),
        text_fill=QColor("#fff3d9"),
        text_shadow=QColor(24, 14, 0, 170),
        ribbon_fill=QColor(28, 22, 52, 220),
        ribbon_outline=QColor("#f0a73f"),
        waveform=QColor(240, 167, 63, 60),
    ),
    Variant(
        slug="findus_cat_exact_silver",
        label="Exact Silver",
        ring_dark=QColor("#1a1a1a"),
        ring_light=QColor("#a2a2a2"),
        badge_inner=QColor("#6c6c6c"),
        accent=QColor("#d8d8d8"),
        text_fill=QColor("#f7f7f7"),
        text_shadow=QColor(0, 0, 0, 180),
        ribbon_fill=QColor(24, 24, 24, 205),
        ribbon_outline=QColor("#c8c8c8"),
        waveform=QColor(255, 255, 255, 0),
        monochrome=True,
        exact_badge=True,
        draw_orbits=False,
        compact_ribbon=True,
    ),
    Variant(
        slug="findus_cat_exact_graphite",
        label="Exact Graphite",
        ring_dark=QColor("#111111"),
        ring_light=QColor("#8c8c8c"),
        badge_inner=QColor("#535353"),
        accent=QColor("#d0d0d0"),
        text_fill=QColor("#fafafa"),
        text_shadow=QColor(0, 0, 0, 180),
        ribbon_fill=QColor(8, 8, 8, 210),
        ribbon_outline=QColor("#b5b5b5"),
        waveform=QColor(255, 255, 255, 0),
        monochrome=True,
        exact_badge=True,
        draw_orbits=False,
        compact_ribbon=True,
        exact_level=1,
    ),
    Variant(
        slug="findus_cat_exact_portrait",
        label="Exact Portrait",
        ring_dark=QColor("#131313"),
        ring_light=QColor("#9d9d9d"),
        badge_inner=QColor("#707070"),
        accent=QColor("#dbdbdb"),
        text_fill=QColor("#f7f7f7"),
        text_shadow=QColor(0, 0, 0, 185),
        ribbon_fill=QColor(18, 18, 18, 198),
        ribbon_outline=QColor("#cfcfcf"),
        waveform=QColor(255, 255, 255, 0),
        monochrome=True,
        exact_badge=True,
        draw_orbits=False,
        compact_ribbon=True,
        tiny_ribbon=True,
        exact_level=2,
    ),
    Variant(
        slug="findus_cat_exact_emblem",
        label="Exact Emblem",
        ring_dark=QColor("#101010"),
        ring_light=QColor("#8f8f8f"),
        badge_inner=QColor("#646464"),
        accent=QColor("#d7d7d7"),
        text_fill=QColor("#fafafa"),
        text_shadow=QColor(0, 0, 0, 190),
        ribbon_fill=QColor(10, 10, 10, 192),
        ribbon_outline=QColor("#bcbcbc"),
        waveform=QColor(255, 255, 255, 0),
        monochrome=True,
        exact_badge=True,
        draw_orbits=False,
        compact_ribbon=True,
        tiny_ribbon=True,
        exact_level=3,
    ),
]


def _point(x: float, y: float) -> QPointF:
    return QPointF(float(x), float(y))


def _ensure_fonts() -> str:
    global FONT_FAMILY
    if FONT_FAMILY:
        return FONT_FAMILY
    for font_path in WINDOWS_FONT_PATHS:
        if not font_path.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id >= 0:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                FONT_FAMILY = families[0]
                return FONT_FAMILY
    FONT_FAMILY = "Sans Serif"
    return FONT_FAMILY


def _cat_head_path() -> QPainterPath:
    path = QPainterPath()

    path.moveTo(_point(512, 832))
    left_side = [
        (472, 845),
        (430, 838),
        (388, 820),
        (344, 790),
        (304, 748),
        (272, 703),
        (250, 648),
        (238, 590),
        (238, 532),
        (252, 470),
        (280, 404),
        (312, 348),
        (334, 290),
        (338, 230),
        (320, 174),
        (348, 190),
        (392, 232),
        (430, 282),
        (468, 258),
        (512, 250),
    ]
    right_side = [(1024 - x, y) for x, y in reversed(left_side[:-1])]

    for x, y in left_side:
        path.lineTo(_point(x, y))
    for x, y in right_side:
        path.lineTo(_point(x, y))
    path.closeSubpath()
    return path


def _exact_cat_head_path() -> QPainterPath:
    path = QPainterPath()
    path.moveTo(_point(512, 860))
    left_side = [
        (468, 854),
        (420, 842),
        (376, 820),
        (334, 782),
        (300, 736),
        (278, 680),
        (266, 620),
        (268, 554),
        (284, 480),
        (308, 410),
        (330, 344),
        (340, 272),
        (322, 178),
        (382, 228),
        (430, 286),
        (472, 336),
        (512, 350),
    ]
    right_side = [(1024 - x, y) for x, y in reversed(left_side[:-1])]
    for x, y in left_side:
        path.lineTo(_point(x, y))
    for x, y in right_side:
        path.lineTo(_point(x, y))
    path.closeSubpath()
    return path


def _draw_badge_background(painter: QPainter, variant: Variant) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if variant.exact_badge:
        outer = QRectF(108, 108, 808, 808)
        painter.setBrush(QColor("#202020"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(outer)

        mid = QRectF(122, 122, 780, 780)
        mid_gradient = QLinearGradient(mid.topLeft(), mid.bottomRight())
        mid_gradient.setColorAt(0.0, variant.ring_light)
        mid_gradient.setColorAt(0.5, variant.ring_dark)
        mid_gradient.setColorAt(1.0, variant.ring_light.darker(105))
        painter.setBrush(QBrush(mid_gradient))
        painter.drawEllipse(mid)

        inner = QRectF(164, 164, 696, 696)
        inner_gradient = QRadialGradient(inner.center(), inner.width() * 0.7)
        inner_gradient.setColorAt(0.0, variant.badge_inner.lighter(108))
        inner_gradient.setColorAt(0.84, variant.badge_inner)
        inner_gradient.setColorAt(1.0, variant.badge_inner.darker(118))
        painter.setBrush(QBrush(inner_gradient))
        painter.drawEllipse(inner)

        painter.setPen(QPen(QColor(255, 255, 255, 90), 6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(QRectF(142, 142, 740, 740), 36 * 34, 36 * 110)
        painter.restore()
        return

    outer = QRectF(112, 112, 800, 800)
    ring_gradient = QLinearGradient(outer.topLeft(), outer.bottomRight())
    ring_gradient.setColorAt(0.0, variant.ring_light)
    ring_gradient.setColorAt(0.4, variant.ring_dark)
    ring_gradient.setColorAt(1.0, variant.ring_light.lighter(105))
    painter.setBrush(QBrush(ring_gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(outer)

    inner = QRectF(152, 152, 720, 720)
    fill_gradient = QRadialGradient(inner.center(), inner.width() * 0.62)
    fill_gradient.setColorAt(0.0, variant.badge_inner.lighter(108))
    fill_gradient.setColorAt(0.72, variant.badge_inner)
    fill_gradient.setColorAt(1.0, variant.badge_inner.darker(155))
    painter.setBrush(QBrush(fill_gradient))
    painter.drawEllipse(inner)

    highlight_pen = QPen(variant.ring_light.lighter(120), 8)
    painter.setPen(highlight_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(QRectF(140, 140, 744, 744), 36 * 28, 36 * 140)
    painter.restore()


def _draw_waveform_orbits(painter: QPainter, variant: Variant) -> None:
    if not variant.draw_orbits:
        return
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(variant.waveform, 8)
    painter.setPen(pen)
    for y_offset, width_scale in ((0, 1.0), (-34, 0.84), (34, 0.84)):
        painter.drawArc(
            QRectF(210, 250 + y_offset, 600 * width_scale, 360),
            36 * 10,
            36 * 120,
        )
    painter.restore()


def _draw_cat(painter: QPainter, variant: Variant) -> None:
    if variant.exact_badge:
        _draw_exact_cat(painter, variant)
        return
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    shadow_path = _cat_head_path()
    painter.translate(10, 12)
    painter.setBrush(QColor(0, 0, 0, 70))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPath(shadow_path)
    painter.translate(-10, -12)

    cat_fill = QColor("#121212") if not variant.monochrome else QColor("#0f0f0f")
    painter.setBrush(cat_fill)
    painter.drawPath(_cat_head_path())

    painter.setBrush(variant.accent if not variant.monochrome else QColor("#b7b7b7"))
    painter.setPen(Qt.PenStyle.NoPen)
    left_ear = QPainterPath()
    left_ear.moveTo(_point(374, 234))
    left_ear.lineTo(_point(332, 194))
    left_ear.lineTo(_point(354, 282))
    left_ear.closeSubpath()
    right_ear = QPainterPath(left_ear)
    right_ear = QPainterPath()
    right_ear.moveTo(_point(650, 234))
    right_ear.lineTo(_point(692, 194))
    right_ear.lineTo(_point(670, 282))
    right_ear.closeSubpath()
    painter.drawPath(left_ear)
    painter.drawPath(right_ear)

    eye_fill = QColor("#f4f4f4") if variant.monochrome else QColor("#fffaf0")
    eye_pen = QPen(QColor(0, 0, 0, 30), 2)
    painter.setBrush(eye_fill)
    painter.setPen(eye_pen)
    painter.drawEllipse(_point(424, 528), 58, 58)
    painter.drawEllipse(_point(600, 528), 58, 58)

    pupil_fill = QColor("#101010")
    painter.setBrush(pupil_fill)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(402, 488, 22, 72))
    painter.drawEllipse(QRectF(578, 488, 22, 72))
    painter.setBrush(QColor(255, 255, 255, 210))
    painter.drawEllipse(QRectF(409, 502, 6, 12))
    painter.drawEllipse(QRectF(585, 502, 6, 12))

    nose = QPainterPath()
    nose.moveTo(_point(512, 616))
    nose.lineTo(_point(470, 600))
    nose.lineTo(_point(554, 600))
    nose.closeSubpath()
    painter.setBrush(variant.accent if not variant.monochrome else QColor("#d0d0d0"))
    painter.drawPath(nose)

    painter.setPen(QPen(variant.accent if not variant.monochrome else QColor("#d0d0d0"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(_point(512, 614), _point(512, 666))
    painter.drawLine(_point(512, 666), _point(486, 690))
    painter.drawLine(_point(512, 666), _point(538, 690))

    painter.setBrush(variant.accent if not variant.monochrome else QColor("#d0d0d0"))
    painter.drawEllipse(QRectF(474, 692, 76, 38))

    whisker_pen = QPen(variant.accent if not variant.monochrome else QColor("#c9c9c9"), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(whisker_pen)
    whiskers = [
        ((468, 648), (304, 620)),
        ((474, 676), (282, 708)),
        ((478, 706), (320, 770)),
        ((556, 648), (720, 620)),
        ((550, 676), (742, 708)),
        ((546, 706), (704, 770)),
    ]
    for start, end in whiskers:
        painter.drawLine(_point(*start), _point(*end))

    fur_pen = QPen(QColor(255, 255, 255, 45) if not variant.monochrome else QColor(255, 255, 255, 28), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(fur_pen)
    fur_marks = [
        ((388, 382), (432, 332)),
        ((454, 432), (486, 396)),
        ((570, 432), (538, 396)),
        ((636, 382), (592, 332)),
        ((368, 552), (314, 572)),
        ((656, 552), (710, 572)),
        ((430, 770), (466, 724)),
        ((512, 792), (512, 734)),
        ((594, 770), (558, 724)),
    ]
    for start, end in fur_marks:
        painter.drawLine(_point(*start), _point(*end))

    painter.restore()


def _draw_exact_cat(painter: QPainter, variant: Variant) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.translate(8, 10)
    painter.setBrush(QColor(0, 0, 0, 72))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPath(_exact_cat_head_path())
    painter.translate(-8, -10)

    painter.setBrush(QColor("#0c0c0c"))
    head_path = _exact_cat_head_path()
    painter.drawPath(head_path)

    accent = QColor("#d4d4d4")
    painter.setBrush(accent)
    painter.setPen(Qt.PenStyle.NoPen)

    left_ear = QPainterPath()
    if variant.exact_level >= 2:
        left_ear.moveTo(_point(364, 254))
        left_ear.lineTo(_point(324, 188))
        left_ear.lineTo(_point(402, 316))
    else:
        left_ear.moveTo(_point(374, 260))
        left_ear.lineTo(_point(332, 198))
        left_ear.lineTo(_point(392, 310))
    left_ear.closeSubpath()
    right_ear = QPainterPath()
    if variant.exact_level >= 2:
        right_ear.moveTo(_point(660, 254))
        right_ear.lineTo(_point(700, 188))
        right_ear.lineTo(_point(622, 316))
    else:
        right_ear.moveTo(_point(650, 260))
        right_ear.lineTo(_point(692, 198))
        right_ear.lineTo(_point(632, 310))
    right_ear.closeSubpath()
    painter.drawPath(left_ear)
    painter.drawPath(right_ear)

    eye_fill = QColor("#efefef")
    painter.setBrush(eye_fill)
    if variant.exact_level >= 2:
        painter.drawEllipse(QRectF(390, 490, 72, 88))
        painter.drawEllipse(QRectF(562, 490, 72, 88))
    else:
        painter.drawEllipse(QRectF(382, 484, 82, 92))
        painter.drawEllipse(QRectF(560, 484, 82, 92))

    painter.setBrush(QColor("#111111"))
    if variant.exact_level >= 2:
        painter.drawEllipse(QRectF(419, 504, 18, 58))
        painter.drawEllipse(QRectF(591, 504, 18, 58))
    else:
        painter.drawEllipse(QRectF(414, 496, 22, 62))
        painter.drawEllipse(QRectF(592, 496, 22, 62))

    painter.setBrush(QColor(255, 255, 255, 220))
    painter.drawEllipse(QRectF(423, 514, 5, 9))
    painter.drawEllipse(QRectF(595, 514, 5, 9))

    nose = QPainterPath()
    nose.moveTo(_point(512, 620))
    nose.lineTo(_point(486, 608))
    nose.lineTo(_point(538, 608))
    nose.closeSubpath()
    painter.setBrush(accent)
    painter.drawPath(nose)

    painter.setPen(QPen(accent, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(_point(512, 620), _point(512, 676))
    painter.drawLine(_point(512, 676), _point(494, 694))
    painter.drawLine(_point(512, 676), _point(530, 694))
    painter.drawArc(QRectF(485, 688, 54, 38), 36 * 190, 36 * 160)

    whisker_pen = QPen(accent, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(whisker_pen)
    whiskers = (
        [
            ((466, 646), (320, 628)),
            ((468, 674), (308, 694)),
            ((474, 700), (336, 736)),
            ((558, 646), (704, 628)),
            ((556, 674), (716, 694)),
            ((550, 700), (688, 736)),
        ]
        if variant.exact_level >= 2
        else [
            ((468, 646), (314, 626)),
            ((470, 676), (302, 698)),
            ((474, 706), (330, 748)),
            ((556, 646), (710, 626)),
            ((554, 676), (722, 698)),
            ((550, 706), (694, 748)),
        ]
    )
    for start, end in whiskers:
        painter.drawLine(_point(*start), _point(*end))

    fur_pen = QPen(QColor(255, 255, 255, 28), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(fur_pen)
    fur_marks = (
        [
            ((404, 396), (444, 350)),
            ((452, 444), (482, 412)),
            ((620, 396), (580, 350)),
            ((572, 444), (542, 412)),
            ((360, 544), (326, 560)),
            ((664, 544), (698, 560)),
            ((430, 800), (466, 746)),
            ((594, 800), (558, 746)),
        ]
        if variant.exact_level >= 2
        else [
            ((396, 388), (438, 342)),
            ((446, 438), (478, 406)),
            ((628, 388), (586, 342)),
            ((578, 438), (546, 406)),
            ((356, 542), (316, 562)),
            ((668, 542), (708, 562)),
            ((438, 794), (472, 744)),
            ((586, 794), (552, 744)),
        ]
    )
    for start, end in fur_marks:
        painter.drawLine(_point(*start), _point(*end))

    if variant.exact_level >= 3:
        painter.setPen(QPen(QColor(255, 255, 255, 38), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(_point(406, 326), _point(356, 286))
        painter.drawLine(_point(618, 326), _point(668, 286))
        painter.drawArc(QRectF(170, 170, 684, 684), 36 * 132, 36 * 96)

    painter.restore()


def _draw_findus_ribbon(painter: QPainter, variant: Variant) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if variant.tiny_ribbon:
        ribbon = QRectF(276, 782, 472, 88)
    elif variant.compact_ribbon:
        ribbon = QRectF(218, 768, 588, 106)
    else:
        ribbon = QRectF(180, 760, 664, 122)
    painter.setPen(QPen(variant.ribbon_outline, 6))
    painter.setBrush(variant.ribbon_fill)
    painter.drawRoundedRect(ribbon, 48, 48)

    if variant.tiny_ribbon:
        font_size = 74
    elif variant.compact_ribbon:
        font_size = 98
    else:
        font_size = 120
    font = QFont(_ensure_fonts(), font_size)
    font.setWeight(QFont.Weight.Black)
    font.setItalic(True)
    painter.setFont(font)
    metrics = QFontMetricsF(font)
    text = "FinDus"
    text_rect = QRectF(ribbon)
    shadow_rect = QRectF(text_rect.adjusted(0, 8, 0, 8))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(variant.text_shadow)
    painter.drawText(shadow_rect, Qt.AlignmentFlag.AlignCenter, text)
    painter.setPen(variant.text_fill)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

    accent_width = metrics.horizontalAdvance("F")
    painter.setPen(QPen(variant.ribbon_outline, 4))
    if variant.tiny_ribbon:
        line_y = 848
    elif variant.compact_ribbon:
        line_y = 844
    else:
        line_y = 856
    painter.drawLine(_point(text_rect.center().x() - accent_width * 1.1, line_y), _point(text_rect.center().x() + accent_width * 1.1, line_y))
    painter.restore()


def _render_variant(variant: Variant) -> QImage:
    image = QImage(ICON_SIZE, ICON_SIZE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    _draw_badge_background(painter, variant)
    _draw_waveform_orbits(painter, variant)
    _draw_cat(painter, variant)
    _draw_findus_ribbon(painter, variant)
    painter.end()
    return image


def _save_variant(image: QImage, slug: str) -> None:
    png_path = OUT_DIR / f"{slug}.png"
    ico_path = OUT_DIR / f"{slug}.ico"
    image.save(str(png_path))
    image.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation).save(str(ico_path))


def _build_contact_sheet(rendered: list[tuple[Variant, QImage]]) -> None:
    cols = 2
    cell = 760
    rows = (len(rendered) + cols - 1) // cols
    width = cell * cols
    height = rows * cell
    sheet = QImage(width, height, QImage.Format.Format_ARGB32)
    sheet.fill(QColor("#101010"))

    painter = QPainter(sheet)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    title_font = QFont(_ensure_fonts(), 30)
    title_font.setWeight(QFont.Weight.Bold)
    painter.setFont(title_font)

    for index, (variant, image) in enumerate(rendered):
        row = index // cols
        col = index % cols
        origin_x = col * cell
        origin_y = row * cell

        card_rect = QRectF(origin_x + 24, origin_y + 24, cell - 48, cell - 48)
        painter.setPen(QPen(QColor(255, 255, 255, 22), 2))
        painter.setBrush(QColor(255, 255, 255, 8))
        painter.drawRoundedRect(card_rect, 28, 28)

        preview = image.scaled(560, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        painter.drawImage(QPointF(origin_x + 100, origin_y + 58), preview)

        painter.setPen(QColor("#f2f2f2"))
        painter.drawText(QRectF(origin_x + 60, origin_y + 630, cell - 120, 60), Qt.AlignmentFlag.AlignCenter, variant.label)

        meta_font = QFont(_ensure_fonts(), 18)
        painter.setFont(meta_font)
        painter.setPen(QColor(255, 255, 255, 130))
        painter.drawText(
            QRectF(origin_x + 60, origin_y + 678, cell - 120, 40),
            Qt.AlignmentFlag.AlignCenter,
            f"{variant.slug}.png / .ico",
        )
        painter.setFont(title_font)

    painter.end()
    sheet.save(str(OUT_DIR / "findus_icon_variant_sheet.png"))


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rendered: list[tuple[Variant, QImage]] = []
    for variant in VARIANTS:
        image = _render_variant(variant)
        _save_variant(image, variant.slug)
        rendered.append((variant, image))

    _build_contact_sheet(rendered)
    print(f"Generated {len(rendered)} icon variants in {OUT_DIR}")
    app.quit()


if __name__ == "__main__":
    main()
