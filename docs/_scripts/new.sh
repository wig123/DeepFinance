#!/bin/bash
#
# new.sh - 新增文档（从模板复制）
#
# Usage:
#   ./docs/_scripts/new.sh <type> <name>
#
# Types:
#   feat <name>     新增功能      → docs/features/<name>/spec.md + state.md + log.md
#   adr <name>      新增 ADR      → docs/decisions/<name>.adr.md
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$DOCS_DIR/_templates"

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <type> <name>"
    echo ""
    echo "Types:"
    echo "  feat <name>     新增功能（spec.md + state.md + log.md）"
    echo "  adr <name>      新增 ADR"
    exit 1
fi

DOC_TYPE="$1"
DOC_NAME="$2"
DATE=$(date +%Y-%m-%d)

replace_date() {
    local file="$1"
    sed -i '' "s/\[日期\]/$DATE/" "$file" 2>/dev/null || sed -i "s/\[日期\]/$DATE/" "$file"
}

create_adr() {
    local name="$1"
    local target_file="$DOCS_DIR/decisions/$name.adr.md"
    local template_file="$TEMPLATES_DIR/decisions/_template.adr.md"

    if [[ -f "$target_file" ]]; then
        echo "文件已存在: $target_file"
        exit 1
    fi

    mkdir -p "$DOCS_DIR/decisions"
    cp "$template_file" "$target_file"
    replace_date "$target_file"
    echo "✅ 创建: $target_file"
}

create_feat() {
    local name="$1"
    local target_dir="$DOCS_DIR/features/$name"
    local template_dir="$TEMPLATES_DIR/features/_template"

    if [[ -d "$target_dir" ]]; then
        echo "目录已存在: $target_dir"
        exit 1
    fi

    mkdir -p "$target_dir"

    # 复制 spec.md, state.md, log.md
    cp "$template_dir/spec.md" "$target_dir/spec.md"
    cp "$template_dir/state.md" "$target_dir/state.md"
    cp "$template_dir/log.md" "$target_dir/log.md"

    replace_date "$target_dir/state.md"

    echo "✅ 创建: $target_dir/"
    echo "✅ 创建: $target_dir/spec.md"
    echo "✅ 创建: $target_dir/state.md"
    echo "✅ 创建: $target_dir/log.md"
}

case $DOC_TYPE in
    adr) create_adr "$DOC_NAME" ;;
    feat) create_feat "$DOC_NAME" ;;
    *)
        echo "未知类型: $DOC_TYPE"
        echo "支持的类型: feat, adr"
        exit 1
        ;;
esac
