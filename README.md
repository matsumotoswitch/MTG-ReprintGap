# MTG-ReprintGap

Scryfallのバルクデータを使用して、Magic: The Gathering (MTG) のカードが再録されるまでの最も長い空白期間（日数）を計算・抽出するPythonスクリプトです。

## 特徴

- デジタル専用セット（MTGOやアリーナ限定）、基本土地、トークン、アートカードなどを自動的に除外して計算します。
- 同一日に発売された別セットのカード重複を排除し、正確な日付単位のギャップを算出します。
- 再録までの期間が 10,000日以上 のカード、または上位30件のカードをランキング形式で標準出力します。

## 動作環境

- Python 3.x
- pandas

## 使い方

1. [Scryfall Bulk Data](https://scryfall.com/docs/api/bulk-data) ページから **Default Cards** のJSONファイルをダウンロードします。
2. ダウンロードしたJSONファイルを `main.py` と同じディレクトリに配置します。
3. `main.py` 内の以下の部分（ファイル名）を、ダウンロードしたファイル名に合わせて変更してください。

   ```python
   DATA_FILE = "default-cards-20260516091059.json"
   ```

4. 必要なライブラリ（`pandas`）をインストールしていない場合はインストールします。

   ```bash
   pip install pandas
   ```

5. スクリプトを実行します。

   ```bash
   python main.py
   ```

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。詳細は `LICENSE.md` をご確認ください。