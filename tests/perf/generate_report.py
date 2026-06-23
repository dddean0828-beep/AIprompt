"""
从 Locust CSV 统计数据生成纯静态 HTML 性能测试报告。

零依赖：不须加载 CDN、不须 JS 模块、不须 HTTP 服务器。
直接用浏览器打开 file:// 即可正常查看。

用法：
  # 先跑 locust 生成 CSV：
  locust -f tests/perf/locustfile.py --headless -u 10 -r 2 --run-time 1m \
    --csv=reports/perf_baseline

  # 再生成静态 HTML 报告：
  python tests/perf/generate_report.py \
    --stats-csv=reports/perf_baseline_stats.csv \
    --history-csv=reports/perf_baseline_stats_history.csv \
    --output=reports/perf_report_baseline.html \
    --scenario="基准测试" \
    --users=10 --rate=2 --duration=1m
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path


# ============================================================
# CSS 样式（内联，零外部依赖）
# ============================================================

CSS = """
:root {
  --bg: #f8f9fa;
  --card-bg: #ffffff;
  --text: #212529;
  --muted: #6c757d;
  --border: #dee2e6;
  --green: #198754;
  --red: #dc3545;
  --orange: #fd7e14;
  --blue: #0d6efd;
  --radius: 8px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  padding: 24px;
}

.container { max-width: 1100px; margin: 0 auto; }

/* 头部 */
.header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  padding: 32px 40px;
  border-radius: var(--radius);
  margin-bottom: 24px;
}
.header h1 { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
.header .meta { font-size: 14px; opacity: 0.75; }

/* 指标卡片 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.kpi-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  text-align: center;
}
.kpi-card .value {
  font-size: 32px;
  font-weight: 700;
  color: var(--blue);
}
.kpi-card .value.green { color: var(--green); }
.kpi-card .value.red { color: var(--red); }
.kpi-card .value.orange { color: var(--orange); }
.kpi-card .label {
  font-size: 13px;
  color: var(--muted);
  margin-top: 4px;
}

/* 表格 */
.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 28px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--blue);
}

table {
  width: 100%;
  border-collapse: collapse;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  font-size: 14px;
}
thead { background: #e9ecef; }
th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
}
td { padding: 8px 12px; border-top: 1px solid var(--border); }
tr:hover td { background: #f1f3f5; }
.num { text-align: right; font-variant-numeric: tabular-nums; }

/* 状态标记 */
.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.badge.ok { background: #d1e7dd; color: var(--green); }
.badge.warn { background: #fff3cd; color: #856404; }
.badge.bad { background: #f8d7da; color: var(--red); }

/* 响应时间进度条 */
.bar-wrap {
  background: #e9ecef;
  border-radius: 4px;
  height: 8px;
  width: 100%;
  margin-top: 2px;
}
.bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--green), var(--blue));
}

/* 页脚 */
.footer {
  text-align: center;
  font-size: 12px;
  color: var(--muted);
  margin-top: 40px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
"""


# ============================================================
# 核心逻辑
# ============================================================

def parse_stats_csv(path: str) -> dict:
    """解析 Locust stats CSV，返回 {endpoint_name: {...}} 和 Aggregated 行"""
    rows = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "").strip()
            rows[name] = {
                "method": row.get("Type", ""),
                "name": name,
                "request_count": int(_safe_float(row.get("Request Count", 0))),
                "failure_count": int(_safe_float(row.get("Failure Count", 0))),
                "median": _safe_float(row.get("Median Response Time", 0)),
                "avg": _safe_float(row.get("Average Response Time", 0)),
                "min": _safe_float(row.get("Min Response Time", 0)),
                "max": _safe_float(row.get("Max Response Time", 0)),
                "content_size": _safe_float(row.get("Average Content Size", 0)),
                "rps": _safe_float(row.get("Requests/s", 0)),
                "failures_per_s": _safe_float(row.get("Failures/s", 0)),
                "p50": _safe_float(row.get("50%", 0)),
                "p66": _safe_float(row.get("66%", 0)),
                "p75": _safe_float(row.get("75%", 0)),
                "p80": _safe_float(row.get("80%", 0)),
                "p90": _safe_float(row.get("90%", 0)),
                "p95": _safe_float(row.get("95%", 0)),
                "p98": _safe_float(row.get("98%", 0)),
                "p99": _safe_float(row.get("99%", 0)),
                "p999": _safe_float(row.get("99.9%", 0)),
                "p9999": _safe_float(row.get("99.99%", 0)),
                "p100": _safe_float(row.get("100%", 0)),
            }
    return rows


def _safe_float(val) -> float:
    """安全转 float，'N/A' 等非数字返回 0"""
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def parse_history_csv(path: str) -> list:
    """解析 Locust history CSV，返回 [{timestamp, ...}, ...]"""
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "timestamp": row.get("Timestamp", ""),
                "user_count": int(row.get("User Count", 0)),
                "total_rps": _safe_float(row.get("Total Requests per second", 0)),
                "failures_per_s": _safe_float(row.get("Total Failure per second", 0)),
                "avg_response": _safe_float(row.get("Average Response Time", 0)),
                "p50": _safe_float(row.get("50%", 0)),
                "p95": _safe_float(row.get("95%", 0)),
                "p99": _safe_float(row.get("99%", 0)),
            })
    return rows


def bar_width(value: float, max_value: float, pct: bool = True) -> str:
    """计算进度条宽度百分比"""
    if max_value == 0:
        return "0%"
    ratio = min(value / max_value, 1.0)
    return f"{ratio * 100:.1f}%"


def classify_response(avg_ms: float) -> tuple:
    """根据平均响应时间分级"""
    if avg_ms < 20:
        return ("ok", "良好")
    elif avg_ms < 50:
        return ("warn", "一般")
    else:
        return ("bad", "慢")


def build_html(stats: dict, history: list, scenario: str,
               users: int, rate: float, duration: str) -> str:
    """构建完整 HTML 文档"""
    agg = stats.get("Aggregated", {})
    if not agg:
        agg = stats.get("", {})

    total_requests = agg.get("request_count", 0)
    total_failures = agg.get("failure_count", 0)
    fail_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    avg_ms = agg.get("avg", 0)
    p50 = agg.get("p50", 0)
    p95 = agg.get("p95", 0)
    p99 = agg.get("p99", 0)
    max_ms = agg.get("max", 0)
    rps = agg.get("rps", 0)

    # 找出最慢的接口（排除 Aggregate 和 prefetch）
    endpoints = {k: v for k, v in stats.items()
                 if k not in ("Aggregated", "") and "prefetch" not in k.lower()}
    slowest = max(endpoints.values(), key=lambda x: x["avg"]) if endpoints else None
    fastest = min(endpoints.values(), key=lambda x: x["avg"]) if endpoints else None

    # KPI 卡片
    kpi_html = f"""
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="value">{total_requests:,}</div>
    <div class="label">总请求数</div>
  </div>
  <div class="kpi-card">
    <div class="value green">{total_failures}</div>
    <div class="label">失败数（失败率 {fail_rate:.2f}%）</div>
  </div>
  <div class="kpi-card">
    <div class="value">{avg_ms:.0f}<span style="font-size:18px"> ms</span></div>
    <div class="label">平均响应时间</div>
  </div>
  <div class="kpi-card">
    <div class="value">{p95:.0f}<span style="font-size:18px"> ms</span></div>
    <div class="label">P95 响应时间</div>
  </div>
  <div class="kpi-card">
    <div class="value">{p99:.0f}<span style="font-size:18px"> ms</span></div>
    <div class="label">P99 响应时间</div>
  </div>
  <div class="kpi-card">
    <div class="value">{rps:.1f}</div>
    <div class="label">每秒请求数 (RPS)</div>
  </div>
</div>
"""

    # 端点详细表格
    table_rows = []
    max_avg = max((v["avg"] for v in endpoints.values()), default=1)
    max_req = max((v["request_count"] for v in endpoints.values()), default=1)

    for ep in sorted(endpoints.values(), key=lambda x: x["avg"], reverse=True):
        status, label = classify_response(ep["avg"])
        bar_pct = ep["avg"] / max_avg * 100 if max_avg > 0 else 0

        table_rows.append(f"""
    <tr>
      <td><span style="font-weight:600">{ep['method']}</span></td>
      <td>{ep['name']}</td>
      <td class="num">{ep['request_count']:,}</td>
      <td class="num">{ep['failure_count']}</td>
      <td class="num">{ep['avg']:.1f} ms</td>
      <td class="num">{ep['p50']:.0f} ms</td>
      <td class="num">{ep['p95']:.0f} ms</td>
      <td class="num">{ep['p99']:.0f} ms</td>
      <td class="num">{ep['max']:.0f} ms</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="bar-wrap"><div class="bar-fill" style="width:{bar_pct:.0f}%"></div></div>
          <span class="badge {status}" style="font-size:11px">{label}</span>
        </div>
      </td>
    </tr>""")

    # 响应时间分布表
    dist_rows = []
    for ep in sorted(endpoints.values(), key=lambda x: x["avg"], reverse=True):
        if ep["name"] in ("Aggregated", ""):
            continue
        dist_rows.append(f"""
    <tr>
      <td><span style="font-weight:600">{ep['method']}</span> {ep['name']}</td>
      <td class="num">{ep['min']:.0f} ms</td>
      <td class="num">{ep['p50']:.0f} ms</td>
      <td class="num">{ep['p75']:.0f} ms</td>
      <td class="num">{ep['p90']:.0f} ms</td>
      <td class="num">{ep['p95']:.0f} ms</td>
      <td class="num">{ep['p99']:.0f} ms</td>
      <td class="num">{ep['max']:.0f} ms</td>
    </tr>""")

    # 吞吐量表
    throughput_rows = []
    for ep in sorted(endpoints.values(), key=lambda x: x["rps"], reverse=True):
        if ep["name"] in ("Aggregated", ""):
            continue
        throughput_rows.append(f"""
    <tr>
      <td><span style="font-weight:600">{ep['method']}</span> {ep['name']}</td>
      <td class="num">{ep['request_count']:,}</td>
      <td class="num">{ep['rps']:.3f} req/s</td>
      <td class="num">{ep['content_size']:,.0f} B</td>
    </tr>""")

    # 查找
    slowest_name = f"{slowest['method']} {slowest['name']}" if slowest else "N/A"
    fastest_name = f"{fastest['method']} {fastest['name']}" if fastest else "N/A"
    fail_cls = "red" if total_failures > 0 else "green"
    fail_label = "异常" if total_failures > 0 else "健康"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>性能测试报告 — {scenario}</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>🔥 性能测试报告：{scenario}</h1>
  <div class="meta">
    👤 {users} 并发用户 &nbsp;|&nbsp;
    📈 孵化率 {rate}/s &nbsp;|&nbsp;
    ⏱ 持续 {duration} &nbsp;|&nbsp;
    🕐 生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  </div>
</div>

{kpi_html}

<h2 class="section-title">📊 端点性能详表（按平均响应时间降序）</h2>
<table>
<thead>
  <tr>
    <th>方法</th><th>接口</th>
    <th class="num">请求数</th><th class="num">失败</th>
    <th class="num">平均</th><th class="num">P50</th><th class="num">P95</th>
    <th class="num">P99</th><th class="num">最大</th>
    <th>响应时间分布</th>
  </tr>
</thead>
<tbody>{''.join(table_rows)}
</tbody>
</table>

<h2 class="section-title">📈 响应时间百分位分布</h2>
<table>
<thead>
  <tr>
    <th>接口</th>
    <th class="num">最小</th><th class="num">P50</th><th class="num">P75</th>
    <th class="num">P90</th><th class="num">P95</th><th class="num">P99</th>
    <th class="num">最大</th>
  </tr>
</thead>
<tbody>{''.join(dist_rows)}
</tbody>
</table>

<h2 class="section-title">🚀 吞吐量</h2>
<table>
<thead>
  <tr><th>接口</th><th class="num">请求总数</th><th class="num">吞吐量</th><th class="num">平均响应大小</th></tr>
</thead>
<tbody>{''.join(throughput_rows)}
</tbody>
</table>

<h2 class="section-title">🔍 综合分析</h2>
<table>
  <tr><td style="width:140px;font-weight:600">总体状态</td>
      <td><span class="badge {fail_cls}">{fail_label}</span></td></tr>
  <tr><td>最慢接口</td><td>{slowest_name}（平均 {slowest['avg']:.1f}ms，P99={slowest['p99']:.0f}ms）</td></tr>
  <tr><td>最快接口</td><td>{fastest_name}（平均 {fastest['avg']:.1f}ms）</td></tr>
  <tr><td>P95 响应</td><td>整体 P95={p95:.0f}ms — {'✅ 优秀（<50ms）' if p95 < 50 else '⚠️ 需关注' if p95 < 200 else '❌ 过高'}</td></tr>
  <tr><td>失败率</td><td>{fail_rate:.2f}% — {'✅ 零失败' if fail_rate == 0 else '❌ 存在失败'}</td></tr>
  <tr><td>响应波动</td><td>P99/P50 = {p99 / p50:.1f}x{' — ✅ 平稳' if p50 > 0 and p99 / p50 < 3 else ' — ⚠️ 存在偶发抖动' if p50 > 0 else ''}</td></tr>
</table>

<div class="footer">
  AI Prompt Manager — Locust 性能测试报告 &nbsp;|&nbsp;
  生成工具: tests/perf/generate_report.py
</div>

</div>
</body>
</html>"""


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="从 Locust CSV 生成纯静态 HTML 性能报告"
    )
    parser.add_argument("--stats-csv", required=True, help="Locust stats CSV 文件路径")
    parser.add_argument("--history-csv", default="", help="Locust stats history CSV（可选）")
    parser.add_argument("--output", required=True, help="输出 HTML 文件路径")
    parser.add_argument("--scenario", default="性能测试", help="场景名称")
    parser.add_argument("--users", type=int, default=0, help="并发用户数")
    parser.add_argument("--rate", type=float, default=0, help="孵化率")
    parser.add_argument("--duration", default="", help="持续时间")
    args = parser.parse_args()

    if not os.path.exists(args.stats_csv):
        print(f"错误: stats CSV 不存在: {args.stats_csv}", file=sys.stderr)
        sys.exit(1)

    stats = parse_stats_csv(args.stats_csv)
    history = parse_history_csv(args.history_csv) if args.history_csv and os.path.exists(args.history_csv) else []

    html = build_html(stats, history, args.scenario,
                      args.users, args.rate, args.duration)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 静态报告已生成: {args.output}")
    print(f"   直接用浏览器打开即可查看（file:// 协议无 CORS 问题）")


if __name__ == "__main__":
    main()
