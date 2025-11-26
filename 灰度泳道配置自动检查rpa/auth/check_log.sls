show_log:
  cmd.run:
    - name: tail -10 /export/servers/jfe/logs/error.log
    - output_loglevel: quiet  # 仅输出命令结果，不显示额外日志