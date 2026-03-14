<script setup lang="ts">
import { computed, ref } from 'vue';
import {
  darkTheme,
  lightTheme,
  NButton,
  NConfigProvider,
  NGlobalStyle,
  NIcon,
  NLoadingBarProvider,
  NMessageProvider,
  useOsTheme,
} from 'naive-ui';
import type { GlobalThemeOverrides } from 'naive-ui';
import { MoonOutline, SunnyOutline } from '@vicons/ionicons5';

const osTheme = useOsTheme();
const isDark = ref(osTheme.value === 'dark');

const toggleTheme = () => {
  isDark.value = !isDark.value;
};

const lightThemeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: 'Inter, -apple-system, sans-serif',
    primaryColor: '#cc7b5d',
    primaryColorHover: '#e08f72',
    primaryColorPressed: '#b5684d',
    bodyColor: '#f5f4ef',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    popoverColor: '#ffffff',
    borderColor: '#e8e6e1',
    textColor1: '#1a1918',
    textColor2: '#575554',
    textColor3: '#8c8b8a',
  },
  Card: {
    borderColor: '#e8e6e1',
    color: '#ffffff',
  },
  Button: {
    colorOpacityPressed: '0.1',
    colorOpacityHover: '0.05',
  },
};

const darkThemeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: 'Inter, -apple-system, sans-serif',
    primaryColor: '#cc7b5d',
    primaryColorHover: '#e08f72',
    primaryColorPressed: '#b5684d',
    bodyColor: '#121211',
    cardColor: '#1e1d1c',
    modalColor: '#1e1d1c',
    popoverColor: '#1e1d1c',
    borderColor: '#302e2d',
    textColor1: '#f5f4ef',
    textColor2: '#a8a6a4',
    textColor3: '#7c7a78',
  },
  Card: {
    borderColor: '#302e2d',
    color: '#1e1d1c',
  },
  Button: {
    colorOpacityPressed: '0.1',
    colorOpacityHover: '0.05',
  },
};

const activeTheme = computed(() => (isDark.value ? darkTheme : lightTheme));
const activeThemeOverrides = computed(() => (isDark.value ? darkThemeOverrides : lightThemeOverrides));
</script>

<template>
  <n-config-provider :theme="activeTheme" :theme-overrides="activeThemeOverrides">
    <n-global-style />
    <n-loading-bar-provider>
      <n-message-provider>
        <div class="app-container" :class="{ 'is-dark': isDark }">
          <header class="app-header">
            <div class="header-content">
              <h1 @click="$router.push('/')">AI Daily</h1>
              <span class="version-badge">Beta</span>
              <div class="header-actions">
                <n-button text style="font-size: 20px" @click="toggleTheme">
                  <n-icon>
                    <moon-outline v-if="!isDark" />
                    <sunny-outline v-else />
                  </n-icon>
                </n-button>
              </div>
            </div>
          </header>
          <main class="app-main animate-fade-up">
            <router-view />
          </main>
          <footer class="app-footer">
            <p>&copy; 2026 AI Daily | Daily AI digest</p>
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
  transition: background-color 0.3s ease, color 0.3s ease;
}

.app-header {
  height: 64px;
  border-bottom: 1px solid var(--n-border-color);
  display: flex;
  align-items: center;
  padding: 0 32px;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
  background-color: rgba(245, 244, 239, 0.85);
  transition: background-color 0.3s ease, border-color 0.3s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.is-dark .app-header {
  background-color: rgba(18, 18, 17, 0.85);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
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
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 500;
  cursor: pointer;
  color: var(--n-text-color);
  letter-spacing: -0.02em;
}

.version-badge {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--n-border-color);
  border-radius: 12px;
  color: var(--n-text-color-3);
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.app-main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 40px 32px;
}

.app-footer {
  padding: 40px 24px;
  border-top: 1px solid var(--n-border-color);
  text-align: center;
  color: var(--n-text-color-3);
  font-size: 14px;
}

@media (max-width: 768px) {
  .app-main {
    padding: 24px 16px;
  }
}
</style>
