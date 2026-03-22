<script setup lang="ts">
import { computed } from 'vue';
import {
  NButton,
  NConfigProvider,
  NGlobalStyle,
  NLoadingBarProvider,
  NMessageProvider,
} from 'naive-ui';
import type { GlobalThemeOverrides } from 'naive-ui';
import { useLocale } from './composables/useLocale';

const { copy, localeToggleLabel, toggleLocale } = useLocale();

const themeOverrides = computed<GlobalThemeOverrides>(() => ({
  common: {
    fontFamily: '"Avenir Next", "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif',
    fontFamilyMono: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
    primaryColor: '#7f6653',
    primaryColorHover: '#6f5949',
    primaryColorPressed: '#604c3e',
    primaryColorSuppl: '#7f6653',
    bodyColor: '#f4ede3',
    cardColor: '#fffdf8',
    modalColor: '#fffdf8',
    popoverColor: '#fffdf8',
    borderColor: 'rgba(73, 58, 45, 0.14)',
    textColorBase: '#201b17',
    textColor1: '#201b17',
    textColor2: '#3c342d',
    textColor3: '#6f665d',
    textColorDisabled: '#9d9388',
    placeholderColor: '#9d9388',
    placeholderColorDisabled: '#b6aea5',
    inputColor: 'rgba(255, 252, 247, 0.96)',
    tableColor: '#fffdf8',
    tableHeaderColor: '#f6efe4',
    actionColor: 'rgba(127, 102, 83, 0.08)',
    actionColorHover: 'rgba(127, 102, 83, 0.12)',
    scrollbarColor: 'rgba(127, 102, 83, 0.22)',
    scrollbarColorHover: 'rgba(127, 102, 83, 0.3)',
    scrollbarWidth: '8px',
    borderRadius: '14px',
    borderRadiusSmall: '10px',
  },
  Button: {
    borderRadiusSmall: '999px',
    borderRadiusMedium: '999px',
    borderRadiusLarge: '999px',
    textColor: '#201b17',
    textColorHover: '#201b17',
    textColorPressed: '#201b17',
    textColorFocus: '#201b17',
    borderHover: '1px solid rgba(73, 58, 45, 0.18)',
    borderPressed: '1px solid rgba(73, 58, 45, 0.22)',
    colorHover: '#f7f1e7',
    colorPressed: '#f1e9dd',
    colorFocus: '#f7f1e7',
  },
  Input: {
    borderHover: '1px solid rgba(73, 58, 45, 0.18)',
    borderFocus: '1px solid rgba(127, 102, 83, 0.3)',
    boxShadowFocus: '0 0 0 3px rgba(127, 102, 83, 0.08)',
    color: 'rgba(255, 252, 247, 0.96)',
  },
  Select: {
    peers: {
      InternalSelection: {
        borderHover: '1px solid rgba(73, 58, 45, 0.18)',
        borderFocus: '1px solid rgba(127, 102, 83, 0.3)',
        boxShadowActive: '0 0 0 3px rgba(127, 102, 83, 0.08)',
        color: 'rgba(255, 252, 247, 0.96)',
      },
    },
  },
  Slider: {
    railColor: 'rgba(127, 102, 83, 0.12)',
    railColorHover: 'rgba(127, 102, 83, 0.18)',
    fillColor: '#7f6653',
    fillColorHover: '#6f5949',
    handleColor: '#fffdf8',
    handleColorHover: '#fffdf8',
    dotColor: '#7f6653',
  },
  Radio: {
    buttonBorderColor: 'rgba(73, 58, 45, 0.12)',
    buttonColor: 'rgba(255, 252, 247, 0.92)',
    buttonTextColor: '#6f665d',
    buttonTextColorActive: '#201b17',
    buttonColorActive: '#f3ebdf',
  },
  Progress: {
    railColor: 'rgba(127, 102, 83, 0.12)',
    color: '#7f6653',
  },
}));
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-global-style />
    <n-loading-bar-provider>
      <n-message-provider>
        <div class="app-shell">
          <a href="#main-content" class="skip-link">{{ copy.app.skipToContent }}</a>

          <header class="site-header">
            <div class="site-header__inner">
              <router-link to="/" class="brand-lockup">
                <span class="brand-lockup__title">AI Daily</span>
                <span class="brand-lockup__subtitle">{{ copy.app.footer }}</span>
              </router-link>

              <nav class="site-nav" aria-label="Primary">
                <router-link to="/" class="site-nav__link" active-class="site-nav__link--active" exact>
                  {{ copy.app.digestNav }}
                </router-link>
                <router-link
                  to="/github"
                  class="site-nav__link"
                  active-class="site-nav__link--active"
                >
                  {{ copy.app.githubNav }}
                </router-link>
              </nav>

              <div class="site-actions">
                <span class="edition-pill">{{ copy.app.beta }}</span>
                <n-button quaternary size="small" class="locale-button" @click="toggleLocale">
                  {{ localeToggleLabel }}
                </n-button>
              </div>
            </div>
          </header>

          <main id="main-content" tabindex="-1" class="site-main">
            <router-view />
          </main>

          <footer class="site-footer">
            <div class="site-footer__inner">
              <p>AI Daily</p>
              <p>{{ copy.app.footer }}</p>
            </div>
          </footer>
        </div>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  color: var(--ink);
}

.skip-link {
  position: absolute;
  top: 12px;
  left: 18px;
  z-index: 20;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--paper-elevated);
  box-shadow: var(--shadow-card);
  text-decoration: none;
  transform: translateY(-160%);
  transition: transform 0.18s ease;
}

.skip-link:focus {
  transform: translateY(0);
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(12px);
  background: rgba(244, 237, 227, 0.8);
  border-bottom: 1px solid rgba(73, 58, 45, 0.08);
}

.site-header__inner,
.site-footer__inner {
  width: min(calc(100% - 32px), var(--max-width));
  margin: 0 auto;
}

.site-header__inner {
  min-height: 78px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.brand-lockup {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-decoration: none;
}

.brand-lockup__title {
  color: var(--ink-strong);
  font-family: var(--font-serif);
  font-size: 1.55rem;
  line-height: 1;
  letter-spacing: -0.04em;
}

.brand-lockup__subtitle {
  color: var(--ink-soft);
  font-size: 0.82rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.site-nav {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: 999px;
  border: 1px solid rgba(73, 58, 45, 0.1);
  background: rgba(255, 252, 246, 0.65);
}

.site-nav__link {
  padding: 10px 16px;
  border-radius: 999px;
  color: var(--ink-soft);
  text-decoration: none;
  font-size: 0.94rem;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.site-nav__link:hover,
.site-nav__link--active {
  color: var(--ink-strong);
  background: rgba(127, 102, 83, 0.1);
}

.site-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.edition-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(73, 58, 45, 0.08);
  background: rgba(255, 252, 246, 0.72);
  color: var(--ink-faint);
  font-size: 0.75rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.locale-button {
  color: var(--ink-soft);
}

.site-main {
  width: min(calc(100% - 32px), var(--max-width));
  margin: 0 auto;
  padding: 34px 0 72px;
}

.site-footer {
  padding: 0 0 28px;
}

.site-footer__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid rgba(73, 58, 45, 0.08);
  color: var(--ink-faint);
  font-size: 0.84rem;
}

.site-footer__inner p {
  margin: 0;
}

@media (max-width: 860px) {
  .site-header__inner {
    flex-wrap: wrap;
    justify-content: center;
    padding: 14px 0;
  }

  .site-actions {
    width: 100%;
    justify-content: center;
  }

  .site-footer__inner {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 560px) {
  .site-main,
  .site-header__inner,
  .site-footer__inner {
    width: min(calc(100% - 20px), var(--max-width));
  }

  .site-nav {
    width: 100%;
    justify-content: center;
  }
}
</style>
