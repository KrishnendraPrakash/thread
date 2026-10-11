"""Native backend entry point; built on each target OS, never in user repositories."""

import json
import signal
import sys

from install_runtime import install

from thread_agent.editor.service import main

if __name__ == "__main__":
    if sys.argv[1:] == ["check-dependencies"]:
        import pathspec
        import pypdf
        import zstandard

        if (
            zstandard.ZstdDecompressor().decompress(
                zstandard.ZstdCompressor().compress(b"native decoder check")
            )
            != b"native decoder check"
        ):
            sys.exit("Bundled decoder check failed.")
        print(
            json.dumps(
                {
                    "frozen": bool(getattr(sys, "frozen", False)),
                    "pathspec": pathspec.__version__,
                    "pypdf": pypdf.__version__,
                    "zstandard": zstandard.__version__,
                }
            )
        )
    elif len(sys.argv) == 3 and sys.argv[1] == "install-runtime":

        def interrupted(signum, frame):
            raise SystemExit(130)

        signal.signal(signal.SIGTERM, interrupted)
        install(sys.argv[2])
    elif len(sys.argv) == 1:
        main()
    else:
        sys.exit("Unknown packaged backend command.")
