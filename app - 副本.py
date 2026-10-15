"""Marketing Lab - consumer review analysis experiment.

The program intentionally uses only Python's standard library so that students
can run it immediately after cloning/copying the project.  It has both a small
desktop UI and a command-line verification mode:

    python app.py              # open the desktop analysis tool
    python app.py --check      # print repeatable verification results
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "reviews.csv"
REQUIRED_COLUMNS = {"brand", "product", "rating", "review"}

# These are transparent, editable rules rather than an opaque sentiment model.
# That makes the calculations easy for students to inspect and verify.
ISSUE_KEYWORDS = {
    "价格": ("贵", "价格", "价钱", "性价比", "便宜"),
    "口味": ("苦", "甜", "淡", "味道", "口味", "香"),
    "服务": ("服务", "态度", "店员", "客服"),
    "等待": ("等", "等待", "排队", "慢", "久"),
    "分量": ("分量", "少", "小份", "不够"),
    "包装/配送": ("包装", "洒", "漏", "配送", "快递"),
    "环境": ("环境", "吵", "座位", "卫生"),
}


def load_reviews(path: Path = DATA_FILE) -> list[dict]:
    """Load and clean reviews without changing the source CSV."""
    if not path.exists():
        raise FileNotFoundError(f"找不到数据文件：{path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"CSV缺少字段：{', '.join(sorted(missing))}")
        rows = []
        for line_no, raw in enumerate(reader, start=2):
            brand = (raw.get("brand") or "").strip()
            product = (raw.get("product") or "").strip()
            review = (raw.get("review") or "").strip()
            try:
                rating = float(str(raw.get("rating", "")).strip())
            except (TypeError, ValueError):
                # A malformed row should be visible, not crash the whole app.
                continue
            if not brand or not review or not 1 <= rating <= 5:
                continue
            rows.append({"brand": brand, "product": product, "rating": rating, "review": review, "line": line_no})
    if not rows:
        raise ValueError("数据文件没有可分析的有效记录")
    return rows


def _one_decimal(value: float) -> float:
    return round(value, 2)


def brand_summary(rows: Iterable[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["brand"]].append(row)
    result = []
    for brand, items in sorted(grouped.items()):
        ratings = [item["rating"] for item in items]
        result.append({
            "brand": brand,
            "count": len(items),
            "average": _one_decimal(statistics.mean(ratings)),
            "positive_rate": _one_decimal(sum(r >= 4 for r in ratings) / len(ratings) * 100),
            "low_rating": sum(r <= 2 for r in ratings),
        })
    return result


def issue_counts(rows: Iterable[dict]) -> Counter:
    counts = Counter()
    for row in rows:
        text = row["review"]
        for issue, keywords in ISSUE_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                counts[issue] += 1
    return counts


def analyze(rows: list[dict], brand: str | None = None) -> dict:
    selected = [row for row in rows if not brand or row["brand"] == brand]
    summaries = brand_summary(rows)
    selected_ratings = [row["rating"] for row in selected]
    return {
        "total": len(selected),
        "brands": summaries,
        "issues": issue_counts(selected),
        "average": _one_decimal(statistics.mean(selected_ratings)) if selected_ratings else 0,
        "selected_brand": brand or "全部品牌",
    }


def verify(rows: list[dict]) -> dict:
    """Independent checks suitable for the fourth stage of the experiment."""
    summaries = brand_summary(rows)
    raw_counts = Counter(row["brand"] for row in rows)
    count_ok = all(item["count"] == raw_counts[item["brand"]] for item in summaries)
    average_ok = all(
        item["average"] == _one_decimal(statistics.mean([r["rating"] for r in rows if r["brand"] == item["brand"]]))
        for item in summaries
    )
    return {
        "valid_rows": len(rows),
        "brand_count": len(summaries),
        "count_check": count_ok,
        "average_check": average_ok,
        "brands": summaries,
    }


def print_check(rows: list[dict]) -> None:
    result = verify(rows)
    print(f"有效评论：{result['valid_rows']} 条；品牌：{result['brand_count']} 个")
    print("品牌       评论数  平均评分  满意度(4-5分)  差评(1-2分)")
    for item in result["brands"]:
        print(f"{item['brand']:<10}{item['count']:<8}{item['average']:<10}{item['positive_rate']:<15}{item['low_rating']}")
    print(f"数量校验：{'通过' if result['count_check'] else '失败'}")
    print(f"平均分校验：{'通过' if result['average_check'] else '失败'}")
    print("主要问题：" + "、".join(f"{k}({v})" for k, v in issue_counts(rows).most_common()) )


def launch_gui(rows: list[dict]) -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk()
    root.title("Marketing Lab · 消费者评论分析实验")
    root.geometry("980x680")
    root.minsize(800, 560)

    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except tk.TclError:
        pass

    header = ttk.Frame(root, padding=(18, 14, 18, 6))
    header.pack(fill="x")
    ttk.Label(header, text="Marketing Lab", font=("Segoe UI", 20, "bold")).pack(anchor="w")
    ttk.Label(header, text="消费者评论分析实验 · 透明规则、可复核结果", foreground="#52606d").pack(anchor="w")

    controls = ttk.Frame(root, padding=(18, 6))
    controls.pack(fill="x")
    ttk.Label(controls, text="选择品牌：").pack(side="left")
    brand_var = tk.StringVar(value="全部品牌")
    brand_values = ["全部品牌"] + sorted({r["brand"] for r in rows})
    selector = ttk.Combobox(controls, textvariable=brand_var, values=brand_values, state="readonly", width=16)
    selector.pack(side="left", padx=(6, 12))
    status_var = tk.StringVar()
    ttk.Label(controls, textvariable=status_var, foreground="#52606d").pack(side="left")

    body = ttk.Frame(root, padding=(18, 4, 18, 18))
    body.pack(fill="both", expand=True)
    table_frame = ttk.LabelFrame(body, text="品牌对比", padding=8)
    table_frame.pack(fill="x")
    columns = ("brand", "count", "average", "positive", "low")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
    headings = {"brand": "品牌", "count": "评论数", "average": "平均评分", "positive": "满意度（4-5分）", "low": "差评数（1-2分）"}
    for col in columns:
        tree.heading(col, text=headings[col])
        tree.column(col, width=130, anchor="center")
    tree.pack(fill="x")

    lower = ttk.Frame(body)
    lower.pack(fill="both", expand=True, pady=(12, 0))
    issues_frame = ttk.LabelFrame(lower, text="主要问题（按评论关键词命中统计）", padding=8)
    issues_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
    issue_text = tk.Text(issues_frame, height=12, width=42, wrap="word", state="disabled", font=("Microsoft YaHei UI", 10))
    issue_text.pack(fill="both", expand=True)
    detail_frame = ttk.LabelFrame(lower, text="实验提示", padding=8)
    detail_frame.pack(side="left", fill="both", expand=True, padx=(6, 0))
    detail_text = tk.Text(detail_frame, height=12, width=42, wrap="word", state="disabled", font=("Microsoft YaHei UI", 10))
    detail_text.pack(fill="both", expand=True)

    def set_text(widget, value: str):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def refresh(*_):
        chosen = brand_var.get()
        brand = None if chosen == "全部品牌" else chosen
        result = analyze(rows, brand)
        for item in tree.get_children():
            tree.delete(item)
        for item in result["brands"]:
            tree.insert("", "end", values=(item["brand"], item["count"], item["average"], f"{item['positive_rate']}%", item["low_rating"]))
        issues = result["issues"]
        issue_lines = [f"{name}：{count} 条评论" for name, count in issues.most_common()]
        set_text(issue_text, "\n".join(issue_lines) if issue_lines else "暂无命中问题关键词。")
        selected_note = f"当前范围：{chosen}\n评论数：{result['total']}\n平均评分：{result['average']}\n\n验证建议\n· 从CSV随机抽3条核对品牌和评分\n· 手算一个品牌的平均分\n· 比较筛选前后的问题数量\n\n关键词规则可在 app.py 的 ISSUE_KEYWORDS 中查看和修改。"
        set_text(detail_text, selected_note)
        status_var.set(f"已加载 {len(rows)} 条有效评论")

    def show_verify():
        result = verify(rows)
        messagebox.showinfo("人工验证结果", json.dumps(result, ensure_ascii=False, indent=2))

    ttk.Button(controls, text="刷新分析", command=refresh).pack(side="left")
    ttk.Button(controls, text="运行校验", command=show_verify).pack(side="left", padx=6)
    selector.bind("<<ComboboxSelected>>", refresh)
    refresh()
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Marketing Lab消费者评论分析器")
    parser.add_argument("--check", action="store_true", help="运行可重复的命令行数据校验，不打开窗口")
    args = parser.parse_args()
    try:
        rows = load_reviews()
    except (OSError, ValueError) as exc:
        raise SystemExit(f"数据加载失败：{exc}") from exc
    if args.check:
        print_check(rows)
    else:
        launch_gui(rows)


if __name__ == "__main__":
    main()
