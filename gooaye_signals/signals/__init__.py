"""signals — 一個訊號一個檔，registry.discover() 自動探索。

每個檔案必須 export 一個模組級 `SIGNAL: SignalSpec`，且 `SIGNAL.id == 檔名`。
底線開頭的檔（_template.py）會被 registry 跳過。
新增訊號：複製 _template.py 或最接近的既有訊號檔，改內容即可。
"""
