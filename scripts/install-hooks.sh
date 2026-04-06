#!/bin/bash
# mainブランチへの直接push禁止フックをインストール

HOOK_FILE="$(git rev-parse --show-toplevel)/.git/hooks/pre-push"

cat > "$HOOK_FILE" << 'HOOK'
#!/bin/bash
# mainブランチへの直接pushを禁止する
# PRを通じたマージのみ許可

current_branch=$(git symbolic-ref HEAD 2>/dev/null | sed 's|refs/heads/||')
remote="$1"

while read local_ref local_sha remote_ref remote_sha; do
    if echo "$remote_ref" | grep -q "refs/heads/main"; then
        if [ "$current_branch" = "main" ]; then
            echo ""
            echo "ERROR: mainブランチへの直接pushは禁止されています。"
            echo ""
            echo "正しい手順:"
            echo "  1. git checkout -b feature/xxx"
            echo "  2. 開発・コミット"
            echo "  3. git push origin feature/xxx"
            echo "  4. GitHub上でPull Requestを作成"
            echo "  5. CI通過後にマージ"
            echo ""
            echo "詳細: docs/OPERATIONS.md の「バージョン管理・リリース」を参照"
            echo ""
            exit 1
        fi
    fi
done

exit 0
HOOK

chmod +x "$HOOK_FILE"
echo "pre-push hook installed: mainへの直接push禁止が有効になりました"
