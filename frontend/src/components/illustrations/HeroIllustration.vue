<script setup lang="ts">
/*
 * 首屏装饰插画：三张悬浮资源卡 + 虚线轨迹 + 光晕。
 * 纯 SVG 几何，无外部素材与授权风险；颜色全部走主题令牌，改品牌色只改一处。
 * 纯装饰，因此对辅助技术隐藏（alt 语义由 aria-hidden 承担）。
 */
</script>

<template>
  <svg class="hero-illustration" viewBox="0 0 640 420" aria-hidden="true" focusable="false">
    <defs>
      <radialGradient id="lh-hero-glow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95" />
        <stop offset="68%" stop-color="#ffffff" stop-opacity="0.34" />
        <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
      </radialGradient>
      <filter id="lh-hero-shadow" x="-25%" y="-25%" width="150%" height="150%">
        <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#0f2a5f" flood-opacity="0.14" />
      </filter>
    </defs>

    <circle class="glow" cx="372" cy="196" r="190" fill="url(#lh-hero-glow)" />

    <path class="trail" d="M64 344 C 200 316, 330 226, 566 96" />

    <!-- 文档卡 -->
    <g class="card-group" transform="rotate(7 418 120)">
      <rect class="card" x="330" y="64" width="176" height="112" rx="18" filter="url(#lh-hero-shadow)" />
      <rect class="chip-violet" x="350" y="86" width="44" height="16" rx="8" />
      <rect class="line-strong" x="350" y="114" width="120" height="8" rx="4" />
      <rect class="line-soft" x="350" y="128" width="96" height="8" rx="4" />
      <rect class="line-soft" x="350" y="142" width="110" height="8" rx="4" />
    </g>

    <!-- 视频卡 -->
    <g class="card-group" transform="rotate(-9 182 202)">
      <rect class="card" x="84" y="140" width="196" height="124" rx="20" filter="url(#lh-hero-shadow)" />
      <rect class="chip-primary" x="104" y="160" width="56" height="18" rx="9" />
      <circle class="play" cx="182" cy="208" r="26" />
      <path class="play-tri" d="M174 196 L194 208 L174 220 Z" />
      <rect class="line-strong" x="104" y="242" width="118" height="8" rx="4" />
      <rect class="line-soft" x="104" y="256" width="76" height="8" rx="4" />
    </g>

    <!-- 进度卡 -->
    <g class="card-group" transform="rotate(-5 367 300)">
      <rect class="card" x="272" y="248" width="190" height="104" rx="18" filter="url(#lh-hero-shadow)" />
      <circle class="chip-green" cx="300" cy="276" r="16" />
      <path class="check" d="M292 276 l6 6 12 -12" />
      <rect class="line-strong" x="328" y="266" width="96" height="8" rx="4" />
      <rect class="line-soft" x="328" y="280" width="62" height="8" rx="4" />
      <rect class="track" x="292" y="308" width="150" height="10" rx="5" />
      <rect class="progress-fill" x="292" y="308" width="98" height="10" rx="5" />
    </g>

    <!-- 点缀 -->
    <path class="spark" d="M528 200 l3 11 11 3 -11 3 -3 11 -3 -11 -11 -3 11 -3 z" />
    <path class="spark spark--soft" d="M470 356 l2 8 8 2 -8 2 -2 8 -2 -8 -8 -2 8 -2 z" />
    <circle class="dot" cx="56" cy="118" r="5" />
    <circle class="dot" cx="604" cy="304" r="4" />
  </svg>
</template>

<style scoped>
.hero-illustration {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}

.card {
  fill: var(--lh-surface);
  stroke: var(--lh-primary-border);
  stroke-width: 1.5;
}

.chip-primary {
  fill: var(--lh-primary-soft);
}

.chip-violet {
  fill: var(--lh-accent-violet-soft);
  opacity: 0.55;
}

.chip-green {
  fill: var(--lh-accent-green-soft);
  opacity: 0.65;
}

.play {
  fill: var(--lh-primary);
}

.play-tri {
  fill: var(--lh-surface);
}

.check {
  fill: none;
  stroke: var(--lh-accent-green);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.line-strong {
  fill: var(--lh-control-track);
  opacity: 0.55;
}

.line-soft {
  fill: var(--lh-border);
}

.track {
  fill: var(--lh-surface-subtle);
}

.progress-fill {
  fill: var(--lh-primary);
}

.trail {
  fill: none;
  stroke: var(--lh-primary-border);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-dasharray: 2 9;
  opacity: 0.85;
}

.spark {
  fill: var(--lh-primary);
  opacity: 0.75;
}

.spark--soft {
  fill: var(--lh-primary-border);
  opacity: 1;
}

.dot {
  fill: var(--lh-primary-border);
}
</style>
