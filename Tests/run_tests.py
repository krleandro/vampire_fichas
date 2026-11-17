#!/usr/bin/env python3
"""Executa suítes Lua 5.4 diretamente na lua54x64.dll do Firecast e testes Python."""
import ctypes
import glob
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

DLL_PATH = r"C:\Users\Cliente\AppData\Local\Firecast\lua54x64.dll"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_lua_file(lua_file: str) -> None:
    if not os.path.exists(DLL_PATH):
        raise RuntimeError(f"lua54x64.dll não encontrada em {DLL_PATH}")

    dll = ctypes.CDLL(DLL_PATH)
    dll.luaL_newstate.restype = ctypes.c_void_p
    dll.luaL_openlibs.argtypes = [ctypes.c_void_p]
    dll.luaL_loadbufferx.argtypes = [
        ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p
    ]
    dll.luaL_loadbufferx.restype = ctypes.c_int
    dll.lua_pcallk.argtypes = [
        ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ssize_t, ctypes.c_void_p
    ]
    dll.lua_pcallk.restype = ctypes.c_int
    dll.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
    dll.lua_tolstring.restype = ctypes.c_char_p
    dll.lua_close.argtypes = [ctypes.c_void_p]

    L = dll.luaL_newstate()
    try:
        dll.luaL_openlibs(L)
        root_escaped = ROOT_DIR.replace("\\", "/")
        bootstrap = (
            f'package.path = "{root_escaped}/?.lua;{root_escaped}/?/init.lua;" .. package.path\n'
            f'dofile("{os.path.abspath(lua_file).replace(chr(92), "/")}")\n'
        ).encode("utf-8")

        rc = dll.luaL_loadbufferx(L, bootstrap, len(bootstrap), b"@bootstrap", b"t")
        if rc != 0:
            ln = ctypes.c_size_t(0)
            msg = dll.lua_tolstring(L, -1, ctypes.byref(ln)).decode("utf-8", errors="replace")
            raise AssertionError(f"Erro de compilação em {lua_file}: {msg}")

        rc = dll.lua_pcallk(L, 0, 0, 0, 0, None)
        if rc != 0:
            ln = ctypes.c_size_t(0)
            msg = dll.lua_tolstring(L, -1, ctypes.byref(ln)).decode("utf-8", errors="replace")
            raise AssertionError(f"Falha em {lua_file}:\n{msg}")
        print(f"[PASS] {os.path.relpath(lua_file, ROOT_DIR)}")
    finally:
        dll.lua_close(L)


def main() -> int:
    targets = sys.argv[1:] if len(sys.argv) > 1 else sorted(
        glob.glob(os.path.join(ROOT_DIR, "Tests", "test_*.lua"))
        + glob.glob(os.path.join(ROOT_DIR, "Tests", "test_*.py"))
    )
    if not targets:
        print("Nenhum teste encontrado.")
        return 1

    for target in targets:
        if target.endswith(".lua"):
            run_lua_file(target)
        elif target.endswith(".py") and os.path.abspath(target) != os.path.abspath(__file__):
            res = subprocess.run([sys.executable, target], cwd=ROOT_DIR)
            if res.returncode != 0:
                return res.returncode
            print(f"[PASS] {os.path.relpath(target, ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
