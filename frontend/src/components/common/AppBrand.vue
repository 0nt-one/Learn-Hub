<template>
  <RouterLink class="brand" to="/" aria-label="Learn-Hub 首页">
    <span class="brand__mark" aria-hidden="true"><span></span><span></span></span>
    <span>Learn-Hub</span>
  </RouterLink>
</template>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: var(--lh-text);
  font-size: 22px;
  font-weight: 750;
  letter-spacing: -.035em;
  text-decoration: none;
  white-space: nowrap;
}

.brand__mark {
  position: relative;
  display: inline-block;
  width: 29px;
  height: 30px;
}

.brand__mark span {
  position: absolute;
  top: 2px;
  width: 12px;
  height: 24px;
  border-radius: 4px 4px 2px 2px;
  background: var(--lh-primary);
  transform: skewY(19deg);
}

.brand__mark span:first-child {
  left: 1px;
}

.brand__mark span:last-child {
  left: 15px;
  background: #6da1ff;
  transform: skewY(-19deg);
}

@media (max-width: 767px) {
  .brand {
    font-size: 18px;
  }
}
</style>
