{# 从 Pillar 获取参数，并检查是否为空 #}
{% set gray_domain = pillar.get('gray_domain') %}
{% set gray_swim_lane = pillar.get('gray_swim_lane') %}
{% set gray_ups = pillar.get('gray_ups') %}

{% set config_file = salt['file.read']('/export/servers/jfe/conf/localconfs/all_gray_ups.json') | replace('\n', '\\n') %}

{# 校验参数是否缺失或为空 #}
{% if not gray_domain or not gray_swim_lane or not gray_ups%}
  {% set error_msg = "Error: 'gray_domain' and 'gray_swim_lane' and 'gray_ups' must be provided and cannot be empty!" %}
{% else %}
  {# 检查 /export/servers/jfe/conf/localconfs/all_gray_ups.json 是否包含指定的 gray_domain、 gray_swim_lane 、 gray_ups#}
  {% set has_gray_domain = salt['file.contains']('/export/servers/jfe/conf/localconfs/all_gray_ups.json', gray_domain) %}
  {% set has_gray_swim_lane = salt['file.contains']('/export/servers/jfe/conf/localconfs/all_gray_ups.json', gray_swim_lane) %}
  {% set has_gray_ups = salt['file.contains']('/export/servers/jfe/conf/localconfs/all_gray_ups.json', gray_ups) %}
{% endif %}

check_resolv_template:
  {% if not gray_domain or not gray_swim_lane or not gray_ups%}
  test.fail_without_changes:
    - name: "{{ error_msg }}"
    - result: False
    - comment: "Please provide 'gray_domain' and 'gray_swim_lane' and 'gray_ups' parameters, e.g., salt '*' state.apply check_resolv_template pillar='{\"gray_domain\": \"8.8.8.8\", \"domain\": \"example.com\"}'"
  {% else %}
  test.configurable_test_state:
    - name: "检查配置文件：/export/servers/jfe/conf/localconfs/all_gray_ups.json  配置项（gray_domain、gray_swim_lane、gray_ups）是否正确"
    - changes: False
    - result: {{ has_gray_domain and has_gray_swim_lane and has_gray_ups}}
    - comment: |
        all_gray_ups.json : {{ config_file }}
  {% endif %}