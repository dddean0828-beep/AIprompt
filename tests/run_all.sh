#!/usr/bin/env bash
# =============================================================================
# AI 提示词管理系统 — 一键全量测试脚本
# =============================================================================
#
# 功能：
#   1. 启动后端（Spring Boot）和前端（Vite）
#   2. 等待服务就绪
#   3. 依次运行：API 测试 → E2E 测试 → Locust 性能测试
#   4. 生成汇总报告
#   5. 停止服务
#
# 用法：
#   bash tests/run_all.sh              # 全量运行
#   bash tests/run_all.sh --api-only   # 仅 API 测试
#   bash tests/run_all.sh --e2e-only   # 仅 E2E 测试
#   bash tests/run_all.sh --perf-only  # 仅性能测试
#   bash tests/run_all.sh --keep-running  # 跑完后不关闭服务
#   bash tests/run_all.sh --browser firefox  # E2E 使用指定浏览器
#
# 依赖：
#   - Java 17+, Maven (mvn)
#   - Node.js, npm
#   - Python 3.9+, pip (pytest, playwright, locust)
#   - MySQL（本地运行，数据库 aiprompt）
# =============================================================================

set -e

# ============================================================
# 颜色输出
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}[INFO]${NC}    $*"; }
success() { echo -e "${GREEN}[OK]${NC}      $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
error()   { echo -e "${RED}[ERROR]${NC}   $*"; }
section() { echo -e "\n${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BOLD}${CYAN}  $*${NC}"; echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ============================================================
# 路径配置
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
TESTS_DIR="$PROJECT_ROOT/tests"
REPORTS_DIR="$TESTS_DIR/reports"

BACKEND_URL="http://localhost:8080"
FRONTEND_URL="http://localhost:5173"

# ============================================================
# 参数解析
# ============================================================
API_ONLY=false
E2E_ONLY=false
PERF_ONLY=false
KEEP_RUNNING=false
BROWSER="chromium"
LOCUST_SCENARIOS="baseline,load"  # 默认跑基准+负载（压力+稳定性耗时较长）
PERF_FULL=false                     # 是否跑全部四组
# $# -> 当前还剩多少个命令行参数
# shift -> 将参数左移一位，$1 变成下一个参数
while [[ $# -gt 0 ]]; do
    case "$1" in    # $1 表示当前要处理的参数，相当于一个指针
        --api-only)   API_ONLY=true; shift ;;   # ;; -> 结束当前 case 分支
        --e2e-only)   E2E_ONLY=true; shift ;;
        --perf-only)  PERF_ONLY=true; shift ;;
        --keep-running) KEEP_RUNNING=true; shift ;;
        --browser)    BROWSER="$2"; shift 2 ;;
        --perf-full)  PERF_FULL=true; shift ;;
        --help|-h)
            echo "用法: bash tests/run_all.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --api-only        仅运行 API 测试"
            echo "  --e2e-only        仅运行 E2E 测试"
            echo "  --perf-only       仅运行性能测试（Locust）"
            echo "  --perf-full       运行全部四组压测场景"
            echo "  --browser <name>  E2E 浏览器 (chromium/firefox/webkit)，默认 chromium"
            echo "  --keep-running    测试完成后不关闭服务"
            echo "  --help            显示此帮助"
            exit 0
            ;;
        *) error "未知选项: $1"; exit 1 ;;  # 相当于 else
    esac
done

# 如果指定了单项，就不启动服务了
if $API_ONLY || $E2E_ONLY || $PERF_ONLY; then
    KEEP_RUNNING=true
fi

# 如果用户指定 perform-only，默认跑全量
if $PERF_ONLY; then
    PERF_FULL=true
fi

# ============================================================
# 结果追踪
# ============================================================
API_RESULT="SKIPPED"
E2E_RESULT="SKIPPED"
PERF_BASELINE_RESULT="SKIPPED"
PERF_LOAD_RESULT="SKIPPED"
PERF_STRESS_RESULT="SKIPPED"
PERF_STABILITY_RESULT="SKIPPED"
START_TIME=$(date +%s)

# ============================================================
# 工具函数
# ============================================================

# if判断调价：检查 URL 是否可访问
#
# curl 参数说明：
#   -s                静默模式，不显示进度条
#   -o /dev/null      丢弃响应内容（只关心状态码）
#   -w "%{http_code}" 输出 HTTP 状态码（如 200、404、500）
#   2>/dev/null       丢弃错误信息（如 Connection refused）
#
# grep 参数说明：
#   -q                只返回匹配结果，不输出内容
#   -E                使用扩展正则
#
# 正则：
#   ^[23]             匹配 2xx、3xx 状态码
#   ^4                匹配 4xx 状态码
#
# 因此：
#   200 -> 成功
#   302 -> 成功
#   404 -> 成功（说明服务已启动，只是资源不存在）
#   500 -> 失败（服务内部错误）
#   无法连接 -> 失败
#
# 当服务返回 2xx、3xx 或 4xx 时，认为服务已经就绪

wait_for_url() {
    local url="$1"      # local 表示局部变量
    local timeout="${2:-60}"    # 如果第二个参数存在，就用第二个参数，否则默认 60 秒
    local interval=2
    local elapsed=0

    info "等待 ${url} 就绪 ..."     # 打印提示信息
    while [[ $elapsed -lt $timeout ]]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -qE '^[23]|^4'; then
            success "${url} 就绪 (${elapsed}s)"
            return 0    # 成功返回
        fi
        sleep "$interval"
        elapsed=$((elapsed + interval))
        echo -n "."
    done
    echo ""
    error "${url} 在 ${timeout}s 内未就绪"
    return 1
}

run_api_tests() {
    section "📡 API 接口测试"

    local report="$REPORTS_DIR/api_report.html"
    local exit_code=0

    cd "$PROJECT_ROOT"
    # --self-contained-html: 把 CSS/JS 嵌入 HTML，单文件可分发
    # tee: 输出同时写入终端和日志文件
    python -m pytest tests/api/ -v \
        --tb=short \
        --strict-markers \
        --html="$report" \
        --self-contained-html \
        --timeout=30 \
        2>&1 | tee "$REPORTS_DIR/api_test.log" || exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        success "API 测试全部通过 ✅"
        API_RESULT="PASSED"
    else
        error "API 测试存在失败 ❌ (exit=$exit_code)"
        API_RESULT="FAILED ($exit_code)"
    fi

    echo ""
    info "API 测试报告: file://${report}"
    return $exit_code
}

run_e2e_tests() {
    section "🌐 E2E 端到端测试"

    local report="$REPORTS_DIR/e2e_report.html"
    local exit_code=0

    cd "$PROJECT_ROOT"
    python -m pytest tests/e2e/ -v \
        --tb=short \
        --strict-markers \
        --browser "$BROWSER" \
        --html="$report" \
        --self-contained-html \
        --timeout=30 \
        2>&1 | tee "$REPORTS_DIR/e2e_test.log" || exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        success "E2E 测试全部通过 ✅"
        E2E_RESULT="PASSED"
    else
        error "E2E 测试存在失败 ❌ (exit=$exit_code)"
        E2E_RESULT="FAILED ($exit_code)"
    fi

    echo ""
    info "E2E 测试报告: file://${report}"
    info "失败截图目录: ${REPORTS_DIR}/e2e_screenshots/"
    return $exit_code
}

run_locust_scenario() {
    local scenario_name="$1"
    local users="$2"
    local rate="$3"
    local duration="$4"
    local description="$5"

    echo ""
    info "🐛 Locust「${scenario_name}」— ${users} 用户 / ${rate}/s / ${duration}"

    local html_report="$REPORTS_DIR/perf_report_${scenario_name}.html"
    local csv_prefix="$REPORTS_DIR/perf_${scenario_name}"

    local exit_code=0
    cd "$PROJECT_ROOT"

    # 第一步：运行 Locust，产出 CSV 原始数据
    python -m locust -f tests/perf/locustfile.py \
        --host "$BACKEND_URL" \
        --headless \
        --users "$users" \
        --spawn-rate "$rate" \
        --run-time "$duration" \
        --csv="$csv_prefix" \
        --loglevel=WARNING \
        2>&1 | tee "$REPORTS_DIR/perf_${scenario_name}.log" || exit_code=$?

    # 第二步：从 CSV 生成纯静态 HTML（可直接 file:// 打开）
    if [[ -f "${csv_prefix}_stats.csv" ]]; then
        python tests/perf/generate_report.py \
            --stats-csv="${csv_prefix}_stats.csv" \
            --history-csv="${csv_prefix}_stats_history.csv" \
            --output="$html_report" \
            --scenario="${scenario_name}" \
            --users="$users" --rate="$rate" --duration="$duration" \
            2>&1 || true    # 失败也不要中断运行
    fi

    if [[ $exit_code -eq 0 ]]; then
        success "Locust「${scenario_name}」完成 ✅"
        # tr -> 进行关键词的转换（大小写转换、重复字符的压缩）
        eval "PERF_$(echo "$scenario_name" | tr '[:lower:]' '[:upper:]')_RESULT='PASSED'"
    else
        error "Locust「${scenario_name}」存在失败 ❌"
        eval "PERF_$(echo "$scenario_name" | tr '[:lower:]' '[:upper:]')_RESULT='FAILED'"
    fi

    info "性能报告: file://${html_report}"
    return $exit_code
}

generate_summary() {
    section "📊 测试汇总报告"

    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))

    local summary_md="$REPORTS_DIR/summary_$(date +%Y%m%d_%H%M%S).md"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # 计算通过/失败计数
    local total=0 passed=0 failed=0

    for result in "$API_RESULT" "$E2E_RESULT" "$PERF_BASELINE_RESULT" "$PERF_LOAD_RESULT" "$PERF_STRESS_RESULT" "$PERF_STABILITY_RESULT"; do
        if [[ "$result" != "SKIPPED" ]]; then
            total=$((total + 1))
            if [[ "$result" == "PASSED" ]]; then
                passed=$((passed + 1))
            else
                failed=$((failed + 1))
            fi
        fi
    done

    # 输出到终端
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  AI 提示词管理系统 — 测试执行汇总${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "  执行时间: ${timestamp}"
    echo -e "  总耗时:   ${minutes} 分 ${seconds} 秒"
    echo -e "───────────────────────────────────────────────────────────"
    printf "  %-30s %s\n" "API 接口测试" "[${API_RESULT}]"
    printf "  %-30s %s\n" "E2E 端到端测试 (${BROWSER})" "[${E2E_RESULT}]"
    printf "  %-30s %s\n" "Locust 基准测试 (10u/2r/1m)" "[${PERF_BASELINE_RESULT}]"
    printf "  %-30s %s\n" "Locust 负载测试 (50u/10r/3m)" "[${PERF_LOAD_RESULT}]"
    printf "  %-30s %s\n" "Locust 压力测试 (200u/50r/5m)" "[${PERF_STRESS_RESULT}]"
    printf "  %-30s %s\n" "Locust 稳定性测试 (30u/5r/10m)" "[${PERF_STABILITY_RESULT}]"
    echo -e "───────────────────────────────────────────────────────────"
    echo -e "  通过: ${GREEN}${passed}${NC} / 失败: ${RED}${failed}${NC} / 跳过: $((6 - total))"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  报告目录: file://${REPORTS_DIR}/"
    echo ""

    # 写入 Markdown 汇总
    mkdir -p "$REPORTS_DIR"
    cat > "$summary_md" << EOF
# 测试执行汇总

**执行时间**: ${timestamp}
**总耗时**: ${minutes} 分 ${seconds} 秒

---

## 测试结果

| 测试套件 | 结果 |
|---------|------|
| API 接口测试 | ${API_RESULT} |
| E2E 端到端测试 (${BROWSER}) | ${E2E_RESULT} |
| Locust 基准测试 (10u/2r/1m) | ${PERF_BASELINE_RESULT} |
| Locust 负载测试 (50u/10r/3m) | ${PERF_LOAD_RESULT} |
| Locust 压力测试 (200u/50r/5m) | ${PERF_STRESS_RESULT} |
| Locust 稳定性测试 (30u/5r/10m) | ${PERF_STABILITY_RESULT} |

**通过: ${passed} / 失败: ${failed} / 跳过: $((6 - total))**

---

## 报告文件

- API 测试: [api_report.html](api_report.html)
- E2E 测试: [e2e_report.html](e2e_report.html)
- 基准测试: [perf_report_baseline.html](perf_report_baseline.html)
- 负载测试: [perf_report_load.html](perf_report_load.html)
- 压力测试: [perf_report_stress.html](perf_report_stress.html)
- 稳定性测试: [perf_report_stability.html](perf_report_stability.html)

---

## 环境信息

- 后端: ${BACKEND_URL}
- 前端: ${FRONTEND_URL}
- 浏览器: ${BROWSER}
- Java: $(java -version 2>&1 | head -1 || echo 'N/A')
- Python: $(python --version 2>&1 || echo 'N/A')
- Node.js: $(node --version 2>&1 || echo 'N/A')
EOF

    success "测试汇总已保存: ${summary_md}"
    echo ""
}

cleanup() {
    info "清理中 ..."

    # 关闭前端
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        info "关闭前端 (PID: $FRONTEND_PID) ..."
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
    fi

    # 关闭后端
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        info "关闭后端 (PID: $BACKEND_PID) ..."
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi

    success "服务已关闭"
}

# 捕获中断信号，确保清理
trap 'echo ""; warn "收到中断信号"; cleanup; exit 1' INT TERM

# ============================================================
# 前置检查
# ============================================================

check_dependency() {
    local name="$1"
    local check_cmd="$2"
    local install_hint="$3"

    if ! eval "$check_cmd" &>/dev/null; then
        error "缺少依赖: ${name}"
        info "安装方式: ${install_hint}"
        return 1
    fi
    success "依赖就绪: ${name}"
}

section "🔍 环境检查"

check_dependency "Python 3" "python --version" "brew install python" || exit 1
check_dependency "Java" "java --version" "brew install openjdk@17" || exit 1
check_dependency "Maven" "mvn --version" "brew install maven" || exit 1
check_dependency "Node.js" "node --version" "brew install node" || exit 1

# 检查 Python 包
info "检查 Python 依赖 ..."
cd "$TESTS_DIR"
if [[ ! -d ".venv" ]]; then
    warn "未创建虚拟环境，正在创建 ..."
    python -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
success "Python 依赖就绪"

# 检查 Playwright 浏览器
if ! playwright install --dry-run "$BROWSER" &>/dev/null; then
    warn "Playwright 浏览器未安装，正在安装 ${BROWSER} ..."
    playwright install "$BROWSER"
fi

echo ""

# ============================================================
# 启动服务（非 --api-only/--e2e-only/--perf-only 时需要）
# ============================================================

NEED_BACKEND=false
NEED_FRONTEND=false

if $API_ONLY; then
    NEED_BACKEND=true
elif $E2E_ONLY; then
    NEED_BACKEND=true
    NEED_FRONTEND=true
elif $PERF_ONLY; then
    NEED_BACKEND=true
else
    NEED_BACKEND=true
    NEED_FRONTEND=true
fi

# 检查服务是否已在运行
check_backend_running() {
    curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/user/login" 2>/dev/null | grep -qE '^[234]' && return 0 || return 1
}

check_frontend_running() {
    curl -s -o /dev/null "$FRONTEND_URL" 2>/dev/null && return 0 || return 1
}

if $NEED_BACKEND; then
    if check_backend_running; then
        success "后端已在运行: ${BACKEND_URL}"
    else
        section "🚀 启动 Spring Boot 后端"
        cd "$BACKEND_DIR"
        mvn spring-boot:run -q &
        BACKEND_PID=$!
        info "后端 PID: $BACKEND_PID"
        wait_for_url "${BACKEND_URL}/api/user/login" 90 || { error "后端启动失败"; exit 1; }
    fi
fi

if $NEED_FRONTEND; then
    if check_frontend_running; then
        success "前端已在运行: ${FRONTEND_URL}"
    else
        section "🚀 启动 Vite 前端"
        cd "$FRONTEND_DIR"
        npm run dev -- --host &
        FRONTEND_PID=$!
        info "前端 PID: $FRONTEND_PID"
        wait_for_url "${FRONTEND_URL}" 60 || { error "前端启动失败"; cleanup; exit 1; }
    fi
fi

# ============================================================
# 创建报告目录
# ============================================================
mkdir -p "$REPORTS_DIR"

# ============================================================
# 运行测试
# ============================================================

API_EXIT=0
E2E_EXIT=0
PERF_EXIT=0

if $E2E_ONLY || $PERF_ONLY; then
    info "跳过 API 测试（--${E2E_ONLY:+e2e}${PERF_ONLY:+perf}-only）"
else
    run_api_tests || API_EXIT=$?
fi

if $API_ONLY || $PERF_ONLY; then
    info "跳过 E2E 测试（--${API_ONLY:+api}${PERF_ONLY:+perf}-only）"
else
    run_e2e_tests || E2E_EXIT=$?
fi

if $API_ONLY || $E2E_ONLY; then
    info "跳过性能测试（--${API_ONLY:+api}${E2E_ONLY:+e2e}-only）"
else
    section "🔥 Locust 性能测试"

    # 基准测试
    run_locust_scenario "baseline" 10 2 "1m" "基准：确认系统正常运行"
    # 负载测试
    run_locust_scenario "load" 50 10 "3m" "负载：观察响应时间趋势"

    if $PERF_FULL; then
        # 压力测试
        run_locust_scenario "stress" 200 50 "5m" "压力：找到系统瓶颈"
        # 稳定性测试
        run_locust_scenario "stability" 30 5 "10m" "稳定性：长时间运行无内存泄漏"
    else
        info "跳过压力测试和稳定性测试（使用 --perf-full 启用全部四组）"
    fi
fi

# ============================================================
# 汇总报告
# ============================================================
generate_summary

# ============================================================
# 清理服务
# ============================================================
if ! $KEEP_RUNNING; then
    section "🛑 停止服务"
    cleanup
else
    info "服务保持运行（--keep-running）"
fi

echo ""
echo -e "${GREEN}${BOLD}✅ 全量测试执行完成！${NC}"
echo -e "   报告目录: file://${REPORTS_DIR}/"
echo ""

# 如果任何测试失败，以非 0 退出
OVERALL_EXIT=0
if [[ "$API_RESULT" == FAILED* ]] || [[ "$E2E_RESULT" == FAILED* ]] || \
   [[ "$PERF_BASELINE_RESULT" == FAILED* ]] || [[ "$PERF_LOAD_RESULT" == FAILED* ]] || \
   [[ "$PERF_STRESS_RESULT" == FAILED* ]] || [[ "$PERF_STABILITY_RESULT" == FAILED* ]]; then
    OVERALL_EXIT=1
fi

exit $OVERALL_EXIT
