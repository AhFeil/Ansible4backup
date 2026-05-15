ROOT := justfile_directory()
python_environment := ROOT / ".env"
python_interpreter := python_environment / "bin/python"
uvicorn := python_environment / "bin/uvicorn"
ty_bin := python_environment / "bin/ty"

HTTP_PROXY := "http://192.168.2.205:10808"

@run:
  echo "网页地址： http://localhost:5123/"
  cd "{{justfile_directory()}}" && {{uvicorn}} ansible_api:app --host 0.0.0.0 --port 5123

@analyze:
  {{ty_bin}} check

[env("SERVICE_LANDING_PAGE_CONFIG_FILE", "tests/config_for_test.yaml")]
@test:
  cd "{{justfile_directory()}}" && {{python_interpreter}} -m pytest -s tests/

[arg("model", long="model")]
[arg("small_model", long="small_model")]
[arg("yolo", long="yolo", value="--dangerously-skip-permissions")]
@ai model="deepseek-v4-pro[1m]" small_model="deepseek-v4-flash" yolo="":
  HTTP_PROXY="{{HTTP_PROXY}}" HTTPS_PROXY="{{HTTP_PROXY}}" \
  ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic" \
  ANTHROPIC_AUTH_TOKEN="sk-0be24a67ac69423f997354af79b06812" \
  API_TIMEOUT_MS=3000000 \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
  ANTHROPIC_MODEL="{{model}}" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="{{model}}" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="{{model}}" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL="{{small_model}}" \
  ANTHROPIC_SMALL_FAST_MODEL="{{small_model}}" \
  CLAUDE_CODE_SUBAGENT_MODEL="{{small_model}}" \
  CLAUDE_CLAUDE_CODE_EFFORT_LEVEL=max \
  claude {{yolo}}

# === 常用配方 ===

# 创建一个空 commit ，带提交信息模板
@new:
  git commit --allow-empty --edit

@forget:
  if git diff --quiet HEAD HEAD~1; then \
    git reset --soft HEAD~1 && echo "✅ 空提交已删除"; \
  fi

# 将所有文件 amend
amend:
  cd "{{ROOT}}" && git add . && git commit --amend

# 将所有文件 commit
commit msg:
  cd "{{ROOT}}" && git add . && git commit -m "{{msg}}"

# 统计代码量
cloc:
  cd {{invocation_directory()}} && git ls-files | xargs cloc
