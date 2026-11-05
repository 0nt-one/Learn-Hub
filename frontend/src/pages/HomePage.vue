<script setup lang="ts">
import BaseCard from '../components/common/BaseCard.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ServiceHealthPanel from '../components/common/ServiceHealthPanel.vue'
import StudentLayout from '../layouts/StudentLayout.vue'
</script>

<template>
  <StudentLayout>
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero__copy">
        <p class="eyebrow">学习 · 整理 · 分享</p>
        <h1 id="hero-title">探索更大的<span>学习世界</span></h1>
        <p class="hero__description">在 Learn-Hub，发现优质资源，遇见更好的自己。</p>
        <div class="hero__search">
          <label for="home-search">搜索资源标题</label>
          <input id="home-search" type="search" placeholder="资源目录接入后可以搜索" disabled />
          <span>待接入</span>
        </div>
      </div>
      <div class="hero__art" aria-hidden="true"><div class="hero__book"></div></div>
    </section>

    <div class="section-intro">
      <div><p class="eyebrow">从这里开始</p><h2>你的学习空间</h2></div>
      <p>页面结构预览 · 暂无业务数据</p>
    </div>

    <div class="home-grid">
      <BaseCard class="featured">
        <template #eyebrow>01 · 发现</template>
        <template #title><h2>精选资源</h2></template>
        <div class="feature-art">
          <div><span>等待资源内容</span><h3>让好资源更容易被找到</h3><p>资源接口接入后展示精选或最新资源。</p></div>
        </div>
      </BaseCard>
      <BaseCard class="topics">
        <template #eyebrow>02 · 探索</template>
        <template #title><h2>课程探索</h2></template>
        <p class="card-description">课程目录接入后，按方向发现学习内容。</p>
        <div class="topic-grid" aria-hidden="true">
          <div class="topic topic--blue"><small>探索方向</small><strong>技术与创新</strong></div>
          <div class="topic topic--purple"><small>探索方向</small><strong>思维与方法</strong></div>
          <div class="topic topic--green"><small>探索方向</small><strong>语言与表达</strong></div>
        </div>
        <p class="card-note">方向名称仅演示布局，并非平台课程。</p>
      </BaseCard>
      <BaseCard class="progress">
        <template #eyebrow>03 · 继续</template>
        <template #title><h2>继续学习</h2></template>
        <EmptyState title="从一份资源开始" description="学习记录接入后，你的进度会显示在这里。" symbol="▤" />
      </BaseCard>
      <BaseCard class="favorites">
        <template #eyebrow>04 · 保存</template>
        <template #title><h2>我的收藏</h2></template>
        <EmptyState title="把喜欢的资源放在这里" description="收藏功能接入后，可随时回到这些资源。" symbol="☆" />
      </BaseCard>
    </div>
    <ServiceHealthPanel class="home-health" />
  </StudentLayout>
</template>

<style scoped>
.hero { display: grid; grid-template-columns: 1.2fr .8fr; min-height: 316px; overflow: hidden; border: 1px solid #e3efff; border-radius: 24px; background: radial-gradient(circle at 85% 0%, #badbff, transparent 38%), linear-gradient(110deg, #e6f5ff, #f8fbff 58%, #daeaff); }
.hero__copy { padding: 48px 0 42px 60px; position: relative; z-index: 1; }
.eyebrow { margin: 0 0 10px; color: var(--lh-primary); font-size: 13px; font-weight: 700; }
.hero h1 { margin: 0; font-size: clamp(30px, 3.4vw, 48px); line-height: 1.2; letter-spacing: -.04em; }
.hero h1 span { color: var(--lh-primary); }
.hero__description { margin: 14px 0 28px; color: var(--lh-text-secondary); font-size: 16px; }
.hero__search { display: flex; align-items: center; gap: 12px; width: min(100%, 650px); min-height: 56px; padding: 6px 12px 6px 20px; border: 1px solid #c6d6ef; border-radius: 999px; background: white; }
.hero__search label { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
.hero__search input { flex: 1; min-width: 0; border: 0; background: transparent; color: var(--lh-text-secondary); opacity: 1; }
.hero__search span { flex: none; padding: 10px 15px; border-radius: 999px; background: var(--lh-surface-subtle); color: var(--lh-text-secondary); font-size: 13px; }
.hero__art { position: relative; min-width: 0; }
.hero__art::before { content: ''; position: absolute; width: 360px; height: 360px; right: 0; top: -22px; border: 2px solid rgb(255 255 255 / 65%); border-radius: 50%; box-shadow: 0 0 0 55px rgb(255 255 255 / 16%); }
.hero__book { position: absolute; width: 190px; height: 220px; top: 60px; right: 95px; border-left: 13px solid #0036bd; border-radius: 14px 23px 23px 14px; background: linear-gradient(135deg, #004cff, #4b92ff); transform: rotate(-12deg); box-shadow: 22px 22px 35px rgb(15 75 168 / 18%); }
.hero__book::before, .hero__book::after { content: ''; position: absolute; left: 35px; right: 30px; height: 7px; border-radius: 8px; background: rgb(255 255 255 / 72%); }
.hero__book::before { top: 70px; }.hero__book::after { top: 94px; right: 60px; }
.section-intro { display: flex; justify-content: space-between; align-items: end; gap: 16px; margin: 32px 0 18px; }
.section-intro h2 { margin: 0; font-size: 25px; }.section-intro > p { margin: 0; color: var(--lh-text-secondary); font-size: 12px; }
.home-grid { display: grid; grid-template-columns: repeat(12,minmax(0,1fr)); gap: 20px; }
.featured { grid-column: span 5; grid-row: span 2; }.topics { grid-column: span 7; }.progress { grid-column: span 4; }.favorites { grid-column: span 3; }
.feature-art { display: flex; align-items: end; min-height: 316px; padding: 24px; overflow: hidden; border-radius: 16px; color: white; background: radial-gradient(circle at 80% 25%, #5f9bff, transparent 32%), linear-gradient(135deg, #061b54, #0b4cbd 60%, #237af3); }
.feature-art span { display: inline-block; padding: 5px 10px; border-radius: 999px; background: rgb(255 255 255 / 17%); font-size: 11px; }
.feature-art h3 { margin: 12px 0 8px; font-size: 24px; }.feature-art p { margin: 0; color: #e2edff; font-size: 13px; line-height: 1.6; }
.card-description { margin: 0 0 16px; color: var(--lh-text-secondary); font-size: 13px; }
.topic-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 12px; }
.topic { display: flex; flex-direction: column; height: 130px; padding: 16px; border-radius: 12px; color: white; }
.topic small { font-size: 11px; }.topic strong { margin-top: 9px; font-size: 17px; }
.topic--blue { background: linear-gradient(135deg,#2672ec,#86baff); }.topic--purple { background: linear-gradient(135deg,#6659db,#b6a6ff); }.topic--green { background: linear-gradient(135deg,#14a47e,#8ce3b0); }
.card-note { margin: 10px 0 0; color: var(--lh-text-secondary); font-size: 11px; }
.home-health { margin-top: 20px; }
@media (max-width: 1023px) {
  .hero { grid-template-columns: 1.4fr .6fr; }.hero__copy { padding-left: 36px; }.hero__book { right: 25px; }
  .featured, .topics { grid-column: span 12; grid-row: auto; }.progress, .favorites { grid-column: span 6; }
}
@media (max-width: 767px) {
  .hero { display: block; }.hero__copy { padding: 36px 24px; }.hero__description { font-size: 14px; }.hero__art { display: none; }
  .section-intro { align-items: start; }.section-intro h2 { font-size: 22px; }.section-intro > p { max-width: 120px; text-align: right; }
  .home-grid { display: flex; flex-direction: column; gap: 16px; }
  .feature-art { min-height: 270px; }.topic-grid { grid-template-columns: 1fr; }.topic { height: 92px; }
}
</style>
