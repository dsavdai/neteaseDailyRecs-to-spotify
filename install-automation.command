#!/bin/zsh

project_dir="${0:A:h}"
cd "$project_dir" || exit 1

if [[ ! -x .venv/bin/python || ! -f .env ]]; then
  echo "请先双击 configure.command 完成配置。"
  read -k 1 "?按任意键关闭……"
  exit 1
fi

.venv/bin/python automation.py install
status=$?

echo
if [[ $status -eq 0 ]]; then
  echo "每日自动同步已安装。"
else
  echo "安装失败，请保留此窗口中的错误信息。"
fi
read -k 1 "?按任意键关闭……"
exit $status
