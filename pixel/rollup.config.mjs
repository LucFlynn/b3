import typescript from "@rollup/plugin-typescript";
import terser from "@rollup/plugin-terser";
import gzipPlugin from "rollup-plugin-gzip";

export default {
  input: "src/index.ts",
  output: {
    file: "dist/epi.min.js",
    format: "iife",
    name: "EPI",
    sourcemap: false,
  },
  plugins: [
    typescript({
      tsconfig: "./tsconfig.json",
    }),
    terser({
      compress: {
        drop_console: true,
        drop_debugger: true,
        passes: 2,
      },
      mangle: {
        toplevel: true,
      },
      format: {
        comments: false,
      },
    }),
    gzipPlugin(),
  ],
};
