module.exports = {
  env: {
    NO_COLOR: "1",
    LC_ALL: "C",
  },
  path: ["$TRYSCRIPT_GIT_ROOT/.venv/bin"],
  patterns: {
    VERSION: "v\\d+\\.\\d+\\.\\S+",
  },
  timeout: 15_000,
};
