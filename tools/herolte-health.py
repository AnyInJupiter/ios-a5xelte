#!/usr/bin/env python3
"""herolte-health.py - diz se um log do S7 mostra toque, audio, GPU e Wi-Fi funcionando.

Uso:  python3 tools/herolte-health.py boot.txt [outro.txt ...]
      python3 tools/herolte-health.py bom.txt ruim.txt --diff    (linhas de cada subsistema que so um dos logs tem)

So le arquivos de texto (saida do herolte-log-pull.py). Nada e enviado nem gravado no aparelho.
Os marcadores vem das mensagens do kernel do branch herolte; se o autor mudar o texto, ajuste a tabela.
"""
import re, sys

# subsistema -> (marcadores de sucesso, marcadores de falha)
CHECKS = {
    "toque": ([r"HEROLTE TOUCH: sensing", r"HEROLTE TOUCH: boot status ok=1"],
              [r"HEROLTE TOUCH: no ACK", r"HEROLTE TOUCH: no supply", r"HEROLTE TOUCH: SENSE_ON failed",
               r"HEROLTE TOUCH: boot status ok=0", r"HEROLTE TOUCH: .* failed int="]),
    "audio": ([r"HEROLTE AUDIO: amplifier answered", r"HEROLTE AUDIO: codec: \d+ registers written"],
              [r"HEROLTE AUDIO: amplifier DID NOT ANSWER", r"HEROLTE AUDIO: no /dev/hakios-audio"]),
    "gpu":   ([r"HEROGPU: registered", r"HEROGPU: IOAcceleratorES registered"],
              [r"HEROGPU SELFTEST: GPU not up", r"HEROGPU SELFTEST: buffer failed",
               r"HEROGPU SELFTEST: mapping failed", r"HEROLTE GPU: read fault"]),
    "wifi":  ([r"HEROLTE WIFI: CONNECTED in", r"HEROLTE WIFI: a first scan: 0, "],
              [r"HEROLTE WIFI: not connected after", r"HEROLTE WIFI: the network is lost",
               r"HEROLTE WIFI: no memory", r"HEROLTE WIFI: no mapping for the rings",
               r"HEROLTE WIFI: handshake .* the MIC does not match"]),
}

def verdict(lines, name):
    ok, bad = CHECKS[name]
    got_ok = [l for l in lines if any(re.search(p, l) for p in ok)]
    got_bad = [l for l in lines if any(re.search(p, l) for p in bad)]
    if got_bad and not got_ok:
        return "FALHOU", got_bad
    if got_ok and got_bad:
        return "DUVIDOSO (sucesso e falha no mesmo log)", got_ok + got_bad
    if got_ok:
        return "ok", got_ok
    return "sem informacao (nenhuma mensagem encontrada)", []

def load(path):
    return open(path, errors="replace").read().splitlines()

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    diff = "--diff" in sys.argv
    if not args:
        print(__doc__); sys.exit(1)
    logs = {a: load(a) for a in args}
    for path, lines in logs.items():
        print("== %s (%d linhas)" % (path, len(lines)))
        for name in CHECKS:
            v, ev = verdict(lines, name)
            print("  %-6s %s" % (name, v))
            for l in ev[:3]:
                print("         | " + l.strip()[:150])
    if diff and len(logs) == 2:
        (pa, la), (pb, lb) = logs.items()
        pats = [p for oks, bads in CHECKS.values() for p in oks + bads] + [r"HEROLTE (TOUCH|AUDIO|WIFI|GPU)", r"HEROGPU"]
        rel = lambda L: {re.sub(r"0x[0-9a-f]+|\d+", "#", l.strip()) for l in L if any(re.search(p, l) for p in pats)}
        sa, sb = rel(la), rel(lb)
        print("\n== so em %s:" % pa)
        for l in sorted(sa - sb)[:25]: print("  " + l[:150])
        print("== so em %s:" % pb)
        for l in sorted(sb - sa)[:25]: print("  " + l[:150])

if __name__ == "__main__":
    main()
