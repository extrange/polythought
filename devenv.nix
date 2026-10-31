{
  pkgs,
  ...
}:

{
  # https://devenv.sh/packages/
  packages = with pkgs; [
    check-jsonschema
    uv
  ];

  languages.python = {
    enable = true;
    package = pkgs.python315;
  };

  # Keep the project virtualenv at .venv so editors, Pyright, and CI agree.
  enterShell = ''
    uv sync --frozen
  '';

  git-hooks.hooks = {
    trim-trailing-whitespace.enable = true;
    end-of-file-fixer.enable = true;
    check-yaml.enable = true; # Does not validate schema
    check-added-large-files.enable = true;
    check-case-conflicts.enable = true;
    actionlint.enable = true;
    trufflehog.enable = true;

    # Use the versions pinned in uv.lock rather than Nixpkgs' versions.
    ruff = {
      enable = true;
      package = null;
      entry = "${pkgs.uv}/bin/uv run --frozen ruff check --fix";
    };
    ruff-format = {
      enable = true;
      package = null;
      entry = "${pkgs.uv}/bin/uv run --frozen ruff format";
    };
    pyright = {
      enable = true;
      package = null;
      entry = "${pkgs.uv}/bin/uv run --frozen pyright";
      pass_filenames = false;
    };
    uv-check.enable = true;

    check-renovate = {
      enable = true;
      package = pkgs.check-jsonschema;
      entry = "${pkgs.check-jsonschema}/bin/check-jsonschema --builtin-schema vendor.renovate --regex-variant nonunicode";
      files = "^(renovate\\.(json|json5)|\\.(github|gitlab)/renovate\\.(json|json5))$";
      types_or = [ "json" "yaml" ];
    };
    check-github-workflows = {
      enable = true;
      package = pkgs.check-jsonschema;
      entry = "${pkgs.check-jsonschema}/bin/check-jsonschema --builtin-schema vendor.github-workflows";
      files = "^\\.github/workflows/[^/]+$";
      types = [ "yaml" ];
    };
  };
}
