import nextConfig from "eslint-config-next";

const eslintConfig = [
  ...nextConfig,
  {
    // TanStack Table returns non-memoizable functions by design.
    // This is a known React Compiler false positive.
    files: ["src/components/biblioteca/document-table.tsx"],
    rules: {
      "react-hooks/incompatible-library": "off",
    },
  },
];

export default eslintConfig;
