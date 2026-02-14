import TkEasyGUI as eg
import datetime
from pathlib import Path
from make_receipt import ReceiptGenerator, ReceiptData

# --- GUI設定 ---
WINDOW_TITLE = "領収書作成ツール"
TEMPLATE_FILE = "receipt_template.pdf"

# スタイル定義
STYLES = {
    "title": {"font": ("", 16, "bold"), "pad": (5, 10)},
    "label": {"font": ("", 11), "size": (12, 1)},
    "input": {"font": ("", 12), "size": (45, 1)},
    "button": {"font": ("", 12), "size": (20, 2)}
}

class ReceiptApp:
    def __init__(self):
        self.generator = ReceiptGenerator(TEMPLATE_FILE)
        self.window = self._build_window()

    def _build_window(self) -> eg.Window:
        """ウィンドウのレイアウト構築"""
        today_str = datetime.date.today().strftime("%Y年 %m月 %d日")

        layout = [
            [eg.Text(WINDOW_TITLE, **STYLES["title"])],
            [eg.Frame("入力項目", layout=[
                [
                    eg.Text("宛名：", **STYLES["label"]),
                    eg.InputText(key="name", **STYLES["input"])
                ],
                [
                    eg.Text("発行日：", **STYLES["label"]),
                    eg.InputText(today_str, key="date", **STYLES["input"])
                ],
                [
                    eg.Text("税抜金額：", **STYLES["label"]),
                    eg.InputText(key="amount", enable_events=True, **STYLES["input"]),
                    eg.Text("円", font=STYLES["label"]["font"])
                ],
                [
                    eg.Text("摘要：", **STYLES["label"]),
                    eg.InputText(key="description", **STYLES["input"])
                ]
            ], pad=(5, 5))],
            [eg.HSeparator()],
            [
                eg.Push(),
                eg.Button("作成", key="-CREATE-", **STYLES["button"]),
                eg.Button("終了", key="-EXIT-", **STYLES["button"]),
                eg.Push()
            ]
        ]
        return eg.Window(WINDOW_TITLE, layout, size=(550, 350))

    def _format_currency_input(self, raw_text: str) -> None:
        """金額入力時に3桁区切りカンマを自動挿入"""
        if not raw_text:
            return

        clean_text = raw_text.replace(",", "")
        if clean_text.isnumeric():
            formatted = "{:,}".format(int(clean_text))
            if raw_text != formatted:
                self.window["amount"].update(formatted)

    def _get_validated_data(self, values: dict) -> ReceiptData | None:
        """入力値の検証とデータクラスへの変換"""
        name = values["name"].strip()
        date = values["date"].strip()
        amount_str = values["amount"].replace(",", "")

        if not name or not date:
            eg.popup_error("宛名と発行日は必須です。", title="入力エラー")
            return None

        if not amount_str.isnumeric():
            eg.popup_error("金額は半角数字で入力してください。", title="入力エラー")
            return None

        return ReceiptData(
            date=date,
            name=name,
            amount_tax_excluded=int(amount_str),
            description=values["description"]
        )

    def _save_pdf(self, data: ReceiptData):
        """保存ダイアログを表示してPDFを生成"""
        save_path = eg.popup_get_file(
            "保存先を指定",
            save_as=True,
            no_window=True,
            file_types=(("PDF Files", "*.pdf"),),
            default_extension=".pdf",
            initial_folder=os.getcwd()
        )

        if not save_path:
            return

        try:
            self.generator.generate(save_path, data)
            eg.popup(f"作成完了しました。\n{save_path}", title="成功")
        except FileNotFoundError:
            eg.popup_error(f"テンプレートファイル({TEMPLATE_FILE})が見つかりません。", title="エラー")
        except PermissionError:
            eg.popup_error("ファイルが開かれているため保存できません。", title="エラー")
        except Exception as e:
            eg.popup_error(f"予期せぬエラーが発生しました:\n{e}", title="エラー")

    def run(self):
        """メインループ"""
        while True:
            event, values = self.window.read()

            if event in (eg.WIN_CLOSED, "-EXIT-"):
                break

            if event == "amount":
                self._format_currency_input(values["amount"])

            if event == "-CREATE-":
                valid_data = self._get_validated_data(values)
                if valid_data:
                    self._save_pdf(valid_data)

        self.window.close()

if __name__ == "__main__":
    import os
    app = ReceiptApp()
    app.run()