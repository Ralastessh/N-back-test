"""시스템 TrueType 폰트를 실제 framebuffer 해상도로 렌더링·캐시한다."""
from collections import OrderedDict
from math import ceil


class SharpText:
    """N-back용 중앙 정렬 텍스트. PsychoPy ImageStim에 네이티브 픽셀 텍스처 전달."""
    def __init__(self, win, text="", pos=(0, 0), height=.03, color="white",
                 wrapWidth=1.1, **kwargs):
        from config import NBACK_UI
        self.win = win
        self.text, self.pos, self.height = text, pos, height
        self.color, self.wrapWidth = color, wrapWidth
        self.font_path = NBACK_UI["font_path"]
        self.cache = OrderedDict()

    def prepare(self, text=None, color=None):
        from PIL import Image, ImageDraw, ImageFont, ImageColor
        from psychopy import visual

        text = self.text if text is None else text
        color = self.color if color is None else color
        pixels = int(self.win.size[1])
        key = (text, color, self.height, self.wrapWidth, pixels)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        # 두 배 해상도로 윤곽을 그린 뒤 네이티브 크기로 축소하여 표시한다.
        scale = 2
        font = ImageFont.truetype(self.font_path, max(1, round(self.height * pixels * scale)))
        width = max(1, round(self.wrapWidth * pixels * scale))
        probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        lines = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split():
                candidate = (line + " " + word).strip()
                if line and probe.textlength(candidate, font=font) > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        content = "\n".join(lines)
        spacing = round(font.size * .20)
        bounds = probe.multiline_textbbox((0, 0), content, font=font, spacing=spacing, align="center")
        pad = 4 * scale
        size = (max(1, ceil(bounds[2] - bounds[0] + 2 * pad)),
                max(1, ceil(bounds[3] - bounds[1] + 2 * pad)))
        canvas = Image.new("RGBA", size)
        ImageDraw.Draw(canvas).multiline_text(
            (pad - bounds[0], pad - bounds[1]), content, font=font,
            fill=ImageColor.getrgb(color) + (255,), spacing=spacing, align="center")
        canvas = canvas.resize((max(1, round(size[0] / scale)), max(1, round(size[1] / scale))),
                               Image.Resampling.LANCZOS)
        stimulus = visual.ImageStim(
            self.win, image=canvas, units="height", pos=self.pos,
            size=(canvas.width / pixels, canvas.height / pixels),
            interpolate=False, autoLog=False)
        self.cache[key] = stimulus
        # 장시간 세션에서 GPU 메모리 증가를 제한한다.
        if len(self.cache) > 128:
            self.cache.popitem(last=False)
        return stimulus

    def draw(self):
        if self.text:
            stimulus = self.prepare()
            stimulus.pos = self.pos
            stimulus.draw()
