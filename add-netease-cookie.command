#!/bin/zsh

project_dir="${0:A:h}"
cd "$project_dir" || exit 1
.venv/bin/python set_netease_cookie.py
status=$?
echo
if [ "$status" -eq 0 ]; then
  echo "网易云 Cookie 配置完成。"
else
  echo "网易云 Cookie 尚未配置。"
fi
read -k 1 "?按任意键关闭..."
exit "$status"
