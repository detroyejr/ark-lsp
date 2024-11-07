# Ark LSP Wrapper

Posit's [Ark](https://github.com/posit-dev/ark) for R currently doesn't support (Fall 2024) running the LSP server as a standalone process apart from the kernel. `ark-lsp.py` communicates with the kernel to initalize the LSP and accepts incoming connections from clients like neovim.

```bash
> ./ark-lsp.py --help

usage: ark-lsp.py [-h] [--version] [--timeout TIMEOUT] [--no-cleanup]

A wrapper to expose ark's LSP server.

options:
  -h, --help         show this help message and exit
  --version          Print the version.
  --timeout TIMEOUT  Time to wait for the LSP server.
  --no-cleanup       Don't cleanup ark's runtime metadata.
```

Setup with nvim-lspconfig:

```lua
-- Use ark with nvim-lspconfig.

local lsp = require 'lspconfig'
local configs = require 'lspconfig.configs'

local rpattern = lsp.util.root_pattern(
  "DESCRIPTION",
  "NAMESPACE",
  ".Rbuildignore",
  ".RProj",
  ".Rproj",
  ".rproj"
)

if not configs.ark then
  configs.ark = {
    default_config = {
      cmd = { "path/to/ark-lsp.py" },
      filetypes = { 'r', 'R' },
      single_file_support = true,
      root_dir = function(fname)
        return rpattern(fname) or vim.loop.os_homedir()
      end,
    },
  }
end

lsp.ark.setup {}
```
