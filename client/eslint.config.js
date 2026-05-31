import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    files: ["client/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "script",
      globals: {
        document: "readonly",
        window: "readonly",
        fetch: "readonly",
        localStorage: "readonly",
        FormData: "readonly",
        console: "readonly",
        AbortController: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly"
      }
    },
    rules: {
      "no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
      "no-console": "off"
    }
  }
];