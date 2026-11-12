<script setup lang="ts">
// 自绘矢量资产：透视玻璃片、书本和弧形飘带；不含表单或页面文字。
import { useId } from 'vue'
const id = useId()
const paint = (name: string) => `url(#${id}-${name})`
</script>

<template>
  <!-- 裁掉顶部空画布，让主体能与表单对齐；保留底部反光和飘带尾端。 -->
  <svg class="auth-illustration" viewBox="0 80 800 680" fill="none" aria-hidden="true" focusable="false">
    <defs>
      <linearGradient :id="`${id}-back`" x1="200" y1="230" x2="510" y2="560" gradientUnits="userSpaceOnUse">
        <stop stop-color="#3d9fff" stop-opacity=".55" /><stop offset=".55" stop-color="#c4eaff" stop-opacity=".5" /><stop offset="1" stop-color="#63b6ff" stop-opacity=".3" />
      </linearGradient>
      <linearGradient :id="`${id}-front`" x1="286" y1="300" x2="605" y2="572" gradientUnits="userSpaceOnUse">
        <stop stop-color="#2895ff" stop-opacity=".9" /><stop offset=".45" stop-color="#68baff" stop-opacity=".68" /><stop offset=".77" stop-color="#d5efff" stop-opacity=".66" /><stop offset="1" stop-color="#65baff" stop-opacity=".68" />
      </linearGradient>
      <linearGradient :id="`${id}-edge`" x1="270" y1="310" x2="590" y2="570" gradientUnits="userSpaceOnUse">
        <stop stop-color="white" /><stop offset=".35" stop-color="#b4dcff" /><stop offset=".7" stop-color="white" /><stop offset="1" stop-color="#1d85ff" />
      </linearGradient>
      <linearGradient :id="`${id}-small`" x1="110" y1="340" x2="350" y2="610" gradientUnits="userSpaceOnUse">
        <stop stop-color="white" stop-opacity=".6" /><stop offset=".7" stop-color="#81c1ff" stop-opacity=".25" /><stop offset="1" stop-color="#c5eaff" stop-opacity=".65" />
      </linearGradient>
      <linearGradient :id="`${id}-ribbon`" x1="330" y1="650" x2="676" y2="435" gradientUnits="userSpaceOnUse">
        <stop stop-color="#bfe4ff" stop-opacity=".35" /><stop offset=".35" stop-color="#168fff" stop-opacity=".85" /><stop offset=".67" stop-color="#69beff" stop-opacity=".8" /><stop offset="1" stop-color="#e9f7ff" stop-opacity=".6" />
      </linearGradient>
      <linearGradient :id="`${id}-ribbon-fade`" x1="590" y1="0" x2="785" y2="0" gradientUnits="userSpaceOnUse">
        <stop stop-color="white" /><stop offset=".4" stop-color="#d9d9d9" /><stop offset="1" stop-color="black" />
      </linearGradient>
      <mask :id="`${id}-ribbon-mask`" maskUnits="userSpaceOnUse" x="0" y="0" width="800" height="760" style="mask-type: luminance">
        <rect width="800" height="760" :fill="paint('ribbon-fade')" />
      </mask>
      <linearGradient :id="`${id}-book`" x1="395" y1="390" x2="505" y2="484" gradientUnits="userSpaceOnUse">
        <stop stop-color="white" /><stop offset="1" stop-color="#d7efff" />
      </linearGradient>
      <radialGradient :id="`${id}-floor`"><stop stop-color="#308aff" stop-opacity=".3" /><stop offset="1" stop-color="#99caff" stop-opacity="0" /></radialGradient>
      <filter :id="`${id}-shadow`" x="-40%" y="-30%" width="190%" height="180%">
        <feDropShadow dx="3" dy="16" stdDeviation="16" flood-color="#2173d4" flood-opacity=".13" />
      </filter>
      <filter :id="`${id}-blur`"><feGaussianBlur stdDeviation="9" /></filter>
    </defs>

    <!-- 保持原始比例，避免横向拉伸把飘带推到 SVG 边界之外。 -->
    <g>
    <!-- 背景光晕由页面统一绘制，这里仅保留主体的地面反光。 -->
    <ellipse cx="365" cy="641" rx="360" ry="91" :fill="paint('floor')" />
    <path d="M215 620L500 597L550 708L268 736Z" fill="#8ec6ff" opacity=".16" :filter="paint('blur')" />

    <!-- 后层玻璃，透视上缘 -->
    <path d="M208 244Q208 226 230 219L466 143Q491 136 493 164L493 541Q493 562 468 567L236 595Q211 596 209 571Z"
      :fill="paint('back')" stroke="#8fc5ff" stroke-width="2" :filter="paint('shadow')" />
    <path d="M214 243Q214 229 234 222L467 147Q484 142 487 162" stroke="white" stroke-opacity=".85" stroke-width="2" />

    <!-- 横向小玻璃片 -->
    <path d="M107 333Q107 309 132 316L332 374Q352 380 352 400L352 588Q351 609 328 606L132 588Q108 586 108 563Z"
      :fill="paint('small')" stroke="#c3e2ff" stroke-width="2" />
    <path d="M111 335Q111 315 131 321L328 379" stroke="white" stroke-width="2" />

    <!-- 主玻璃书板：蓝色体积、细边反光 -->
    <path d="M274 312Q274 291 298 284L566 201Q596 191 597 223L597 574Q597 596 570 602L302 626Q276 629 275 602Z"
      :fill="paint('front')" :stroke="paint('edge')" stroke-width="3" :filter="paint('shadow')" />
    <path d="M282 309Q284 295 302 289L565 207" stroke="white" stroke-width="2" stroke-opacity=".9" />
    <path d="M590 226L590 574Q590 589 570 595" stroke="#95d3ff" stroke-width="3" stroke-opacity=".8" />

    <!-- 白色品牌书本，顺着玻璃透视 -->
    <path d="M379 398Q408 386 431 403L431 476Q406 465 380 475Z" :fill="paint('book')" stroke="white" stroke-width="1.5" />
    <path d="M438 401Q463 379 491 380Q496 380 496 386L496 449Q466 449 438 475Z" :fill="paint('book')" stroke="white" stroke-width="1.5" />
    <path d="M435 405V477" stroke="#a7d9ff" stroke-width="2" />

    <!-- 后方轻薄波面 -->
    <path d="M0 530C100 483 223 485 332 537C209 503 111 519 0 577Z" fill="#d3eaff" fill-opacity=".65" />
    <path d="M0 530C100 483 223 485 332 537" stroke="white" stroke-width="2" />

    <!-- 尾端在画布内收细；遮罩同时淡出填充与高光，不影响书本。 -->
    <g :mask="paint('ribbon-mask')">
    <path d="M0 687C218 679 335 630 442 529C535 441 641 321 728 382C750 398 771 426 784 443C744 415 675 451 587 498C441 566 366 687 0 728Z"
      :fill="paint('ribbon')" />
    <path d="M0 687C218 679 335 630 442 529C535 441 641 321 728 382C750 398 771 426 784 443"
      stroke="#75c2ff" stroke-width="3" stroke-opacity=".65" />
    <path d="M0 684C217 676 333 627 440 526C534 438 642 318 730 379C752 395 773 423 785 440"
      stroke="white" stroke-width="2" stroke-opacity=".75" />
    </g>
    </g>
  </svg>
</template>

<style scoped>
.auth-illustration { display: block; width: 100%; height: auto; }
</style>
