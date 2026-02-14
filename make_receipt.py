import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from pypdf import PdfReader, PdfWriter

# --- 設定・定数 ---
FONT_PATH = Path("C:/Windows/Fonts/msgothic.ttc")
FONT_NAME = "JapaneseFont"
TAX_RATE = 0.10

# レイアウト設定 (x, y, font_size)
# original: 本紙, copy: 控え
LAYOUT_CONFIG: Dict[str, Dict[str, Tuple[float, float, int]]] = {
    "original": {
        "name": (20, 240, 14),
        "amount": (90, 220, 16),
        "description": (73, 211.2, 11),
        "date": (145, 273.5, 11),
        "breakdown": (58, 178.3, 11),
        "tax": (58, 172, 11),
    },
    "copy": {
        "name": (20, 105, 14),
        "amount": (90, 87, 16),
        "description": (73, 76.5, 11),
        "date": (145, 139, 11),
        "breakdown": (58, 43.5, 11),
        "tax": (58, 37.5, 11),
    }
}

@dataclass
class ReceiptData:
    """領収書データを管理するデータクラス"""
    date: str
    name: str
    amount_tax_excluded: int
    description: str

    @property
    def tax_amount(self) -> int:
        """消費税額を計算"""
        return int(self.amount_tax_excluded * TAX_RATE)

    @property
    def total_amount(self) -> int:
        """税込合計金額を計算"""
        return self.amount_tax_excluded + self.tax_amount

    def get_formatted_data(self) -> Dict[str, str]:
        """描画用に整形されたデータを返す"""
        return {
            "date": self.date,
            "name": self.name,
            "amount": f"¥{self.total_amount:,}-",
            "tax": f"¥{self.tax_amount:,}",
            "breakdown": f"¥{self.amount_tax_excluded:,}",
            "description": self.description
        }

class ReceiptGenerator:
    """PDF領収書生成クラス"""

    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        self._register_font()

    def _register_font(self) -> bool:
        """フォントの登録処理"""
        if not FONT_PATH.exists():
            print(f"警告: フォントファイルが見つかりません: {FONT_PATH}")
            return False
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))
            return True
        except Exception as e:
            print(f"フォント登録エラー: {e}")
            return False

    def _create_overlay(self, data: ReceiptData) -> Optional[io.BytesIO]:
        """データが記載されたオーバーレイPDF（メモリ上）を作成"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # 描画用データの取得
        draw_items = data.get_formatted_data()

        # 本紙と控えを描画
        for section in ["original", "copy"]:
            config = LAYOUT_CONFIG[section]
            for key, (x, y, size) in config.items():
                if key in draw_items:
                    c.setFont(FONT_NAME, size)
                    c.drawString(x * mm, y * mm, draw_items[key])

        c.save()
        buffer.seek(0)
        return buffer

    def generate(self, output_path: str, data: ReceiptData) -> bool:
        """テンプレートと合成してPDFを保存"""
        if not self.template_path.exists():
            raise FileNotFoundError(f"テンプレートが見つかりません: {self.template_path}")

        overlay_pdf = self._create_overlay(data)
        if not overlay_pdf:
            return False

        try:
            # テンプレート読み込み
            reader = PdfReader(self.template_path)
            writer = PdfWriter()

            # 1ページ目に合成
            page = reader.pages[0]
            overlay_reader = PdfReader(overlay_pdf)
            page.merge_page(overlay_reader.pages[0])
            writer.add_page(page)

            # 保存
            with open(output_path, "wb") as f:
                writer.write(f)
            return True

        except Exception as e:
            print(f"PDF保存エラー: {e}")
            raise e

if __name__ == "__main__":
    # テスト実行用
    test_data = ReceiptData(
        date="2026年 2月 14日",
        name="株式会社 テスト商事",
        amount_tax_excluded=10000,
        description="商品代として"
    )
    generator = ReceiptGenerator("receipt_template.pdf")
    generator.generate("領収書_テスト.pdf", test_data)
    print("テスト完了")