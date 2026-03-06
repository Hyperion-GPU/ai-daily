<script setup lang="ts">
import { darkTheme, NConfigProvider, NGlobalStyle, NLoadingBarProvider, NMessageProvider } from 'naive-ui';
import type { GlobalThemeOverrides } from 'naive-ui';

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#58a6ff',
    primaryColorHover: '#79c0ff',
    primaryColorPressed: '#1f6feb',
    bodyColor: '#0d1117',
    cardColor: '#161b22',
    modalColor: '#161b22',
    popoverColor: '#161b22',
    borderColor: '#30363d',
    textColor1: '#f0f6fc',
    textColor2: '#c9d1d9',
    textColor3: '#8b949e',
  },
  Card: {
    borderColor: '#30363d',
    color: '#161b22',
  },
  Button: {
    colorOpacityPressed: '0.1',
    colorOpacityHover: '0.05',
  },
};
</script>

<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-global-style />
    <n-loading-bar-provider>
      <n-message-provider>
        <div class="app-container">
          <header class="app-header">
            <div class="header-content">
              <h1 @click="$router.push('/')">AI Daily</h1>
              <span class="version-badge">Beta</span>
            </div>
          </header>
          <main class="app-main">
            <router-view />
          </main>
          <footer class="app-footer">
            <p>&copy; 2026 AI Daily | 每日 AI 信息摘要</p>
          </footer>
        </div>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  height: 60px;
  border-bottom: 1px solid #30363d;
  background-color: #161b22;
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
}

h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  cursor: pointer;
  color: #f0f6fc;
}

.version-badge {
  font-size: 12px;
  padding: 2px 8px;
  border: 1px solid #30363d;
  border-radius: 12px;
  color: #8b949e;
}

.app-main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 24px;
}

.app-footer {
  padding: 40px 24px;
  border-top: 1px solid #30363d;
  text-align: center;
  color: #8b949e;
  font-size: 14px;
}

@media (max-width: 768px) {
  .app-main {
    padding: 16px;
  }
}
</style>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji',
    'Segoe UI Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
