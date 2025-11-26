{# 从 Pillar 获取参数，并检查是否为空 #}
{% set gray_domain = pillar.get('gray_domain') %}



{% set config_file = salt['file.read']('/export/servers/jfe/conf/localconfs/all_gray_ups.json') | replace('\n', '\\n') %}

{# 校验参数是否缺失或为空 #}
{% if not gray_domain %}
  {% set error_msg = "Error: 'gray_domain' must be provided and cannot be empty!" %}
{% else %}
  {# 检查 /export/servers/jfe/conf/localconfs/all_gray_ups.json 是否已删除指定的 gray_domain #}
  {% set has_gray_domain = salt['file.contains']('/export/servers/jfe/conf/localconfs/all_gray_ups.json', gray_domain) %}
  {% set check_result = not has_gray_domain %}
{% endif %}

check_delete_template:
  {% if not gray_domain %}
  test.fail_without_changes:
    - name: "{{ error_msg }}"
    - result: False
    - comment: "Please provide 'gray_domain' parameter, e.g., salt '*' state.apply check_resolv_template pillar='{\"gray_domain\": \"color.7fresh.com\", \"gray_swim_lane\": \"GRAY_RETAIL_MAIN\"}'"
  {% else %}
  test.configurable_test_state:
    - name: "检查配置文件：/export/servers/jfe/conf/localconfs/all_gray_ups.json  配置项（gray_domain、gray_swim_lane）是否被删除"
    - changes: False
    - result: {{ check_result }}
    - comment: |
        all_gray_ups.json : {{ config_file }}
        gray_domain 字段存在: {{ has_gray_domain }}
        是否删除配置成功: {{ check_result }}
  {% endif %}