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
    fontFamily: '-apple-system, "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif',
    fontFamilyMono: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
    primaryColor: '#c4956a',
    primaryColorHover: '#b5875e',
    primaryColorPressed: '#a67a54',
    primaryColorSuppl: '#c4956a',
    bodyColor: '#f5f4f1',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    popoverColor: '#ffffff',
    borderColor: 'rgba(0, 0, 0, 0.08)',
    textColorBase: '#191918',
    textColor1: '#191918',
    textColor2: '#3d3d3a',
    textColor3: '#6b6b66',
    textColorDisabled: '#9a9a94',
    placeholderColor: '#9a9a94',
    placeholderColorDisabled: '#bbbbbb',
    inputColor: '#ffffff',
    tableColor: '#ffffff',
    tableHeaderColor: '#f9f8f6',
    actionColor: 'rgba(0, 0, 0, 0.04)',
    actionColorHover: 'rgba(0, 0, 0, 0.06)',
    scrollbarColor: 'rgba(0, 0, 0, 0.15)',
    scrollbarColorHover: 'rgba(0, 0, 0, 0.25)',
    scrollbarWidth: '8px',
    borderRadius: '8px',
    borderRadiusSmall: '6px',
  },
  Button: {
    borderRadiusSmall: '999px',
    borderRadiusMedium: '999px',
    borderRadiusLarge: '999px',
    textColor: '#191918',
    textColorHover: '#191918',
    textColorPressed: '#191918',
    textColorFocus: '#191918',
    borderHover: '1px solid rgba(0, 0, 0, 0.12)',
    borderPressed: '1px solid rgba(0, 0, 0, 0.18)',
    colorHover: '#f2f0ee',
    colorPressed: '#eae8e5',
    colorFocus: '#f2f0ee',
  },
  Input: {
    borderHover: '1px solid rgba(0, 0, 0, 0.15)',
    borderFocus: '1px solid rgba(196, 149, 106, 0.5)',
    boxShadowFocus: '0 0 0 3px rgba(196, 149, 106, 0.08)',
    color: '#ffffff',
  },
  Select: {
    peers: {
      InternalSelection: {
        borderHover: '1px solid rgba(0, 0, 0, 0.15)',
        borderFocus: '1px solid rgba(196, 149, 106, 0.5)',
        boxShadowActive: '0 0 0 3px rgba(196, 149, 106, 0.08)',
        color: '#ffffff',
      },
    },
  },
  Slider: {
    railColor: 'rgba(0, 0, 0, 0.08)',
    railColorHover: 'rgba(0, 0, 0, 0.12)',
    fillColor: '#c4956a',
    fillColorHover: '#b5875e',
    handleColor: '#ffffff',
    handleColorHover: '#ffffff',
    dotColor: '#c4956a',
  },
  Radio: {
    buttonBorderColor: 'rgba(0, 0, 0, 0.10)',
    buttonColor: '#f9f8f6',
    buttonTextColor: '#6b6b66',
    buttonTextColorActive: '#191918',
    buttonColorActive: 'rgba(196, 149, 106, 0.08)',
  },
  Progress: {
    railColor: 'rgba(0, 0, 0, 0.06)',
    color: '#c4956a',
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
  background: rgba(245, 244, 241, 0.88);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
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
  font-family: var(--font-heading);
  font-size: 1.4rem;
  font-weight: 500;
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
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.6);
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
  background: rgba(0, 0, 0, 0.05);
}

.site-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.edition-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.6);
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
  border-top: 1px solid rgba(0, 0, 0, 0.06);
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
