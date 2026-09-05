#!/bin/zsh

project_dir="${0:A:h}"
cd "$project_dir" || exit 1

if [[ ! -x .venv/bin/python ]]; then
  echo "正在创建本地 Python 环境……"
  python3 -m venv .venv || exit 1
  .venv/bin/python -m pip install -r requirements.txt || exit 1
fi

.venv/bin/python setup.py
result=$?

echo
if [[ $result -eq 0 ]]; then
  echo "配置程序已完成。可以关闭此窗口。"
else
  echo "配置程序出现错误。请保留窗口并告诉 Codex 错误类型，不要截图密钥。"
fi
echo "按任意键关闭窗口。"
read -k 1
exit $result
