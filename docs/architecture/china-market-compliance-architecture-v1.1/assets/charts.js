(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var success = style.getPropertyValue('--success').trim();
  var warning = style.getPropertyValue('--warning').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  // --- Chart: Cost Model Comparison ---
  var chartCost = echarts.init(document.getElementById('chart-cost-model'), null, { renderer: 'svg' });

  var categories = ['LLM推理成本', '内容审核成本', '缓存命中率\n影响', '合规人力\n(折算)', '综合成本'];
  var gpt4oData = [100, 0, 100, 0, 100];
  var v10Data = [45, 0, 100, 15, 55];  // v1.0 偏乐观的测算
  var v11Data = [60, 12, 125, 15, 70];  // v1.1 修正后测算

  chartCost.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      axisPointer: { type: 'shadow' },
      formatter: function(params) {
        var html = params[0].axisValue + '<br/>';
        params.forEach(function(p) {
          html += p.marker + p.seriesName + ': ' + p.value + '%<br/>';
        });
        return html;
      }
    },
    legend: {
      data: ['原方案 GPT-4o', 'v1.0 测算', 'v1.1 修正后'],
      bottom: 0,
      textStyle: { color: muted, fontSize: 12 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        color: muted,
        fontSize: 11,
        interval: 0
      },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '相对成本 (%)',
      nameTextStyle: { color: muted, fontSize: 11 },
      axisLabel: {
        color: muted,
        fontSize: 11,
        formatter: '{value}%'
      },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    series: [
      {
        name: '原方案 GPT-4o',
        type: 'bar',
        data: gpt4oData,
        itemStyle: {
          color: muted,
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '22%'
      },
      {
        name: 'v1.0 测算',
        type: 'bar',
        data: v10Data,
        itemStyle: {
          color: warning,
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '22%'
      },
      {
        name: 'v1.1 修正后',
        type: 'bar',
        data: v11Data,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: accent },
            { offset: 1, color: accent2 }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '22%'
      }
    ]
  });

  window.addEventListener('resize', function() {
    chartCost.resize();
  });
})();
