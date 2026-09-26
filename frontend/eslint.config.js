import js from '@eslint/js';
import react from 'eslint-plugin-react';
import globals from 'globals';

// Focus on real defects: undefined identifiers (a missed import crashes a page at runtime),
// unused code, and JSX components that are used but not defined.
export default [
  {ignores: ['dist/**', 'node_modules/**', 'tests/**']},
  js.configs.recommended,
  {
    files: ['src/**/*.{js,jsx}', 'vite.config.js'],
    plugins: {react},
    languageOptions: {ecmaVersion: 2023, sourceType: 'module', globals: {...globals.browser},
      parserOptions: {ecmaFeatures: {jsx: true}}},
    settings: {react: {version: '19'}},
    rules: {
      'react/jsx-no-undef': 'error',
      'react/jsx-uses-vars': 'error',
      'react/jsx-uses-react': 'error',
      'no-undef': 'error',
      'no-unused-vars': ['warn', {args: 'none', caughtErrors: 'none'}],
      'no-empty': ['error', {allowEmptyCatch: true}],
    },
  },
];
