# Verified additional native notices

`zstd-1.5.7-LICENSE` retains the upstream Zstandard BSD license, obtained without a new download from the already installed Homebrew zstd 1.5.7_1 distribution. The approved zstandard 0.25.0 build environment reports its embedded native ZSTD_VERSION as 1.5.7. SHA-256: `7055266497633c9025b777c78eb7235af13922117480ed5c674677adc381c9d8`.

The Python wrapper's own BSD notice is separately included in its distribution metadata. The native build copies this additional library notice only when the embedded library version matches; otherwise provenance records the missing notice. This file does not grant a license for Thread, whose Thread-authored code now uses the owner-approved MIT license; third-party components keep their own terms.

The approved Ollama Mac archive already supplies GO_LICENSE, LLAMA_CPP_LICENSE, LLAMA_CPP_VENDORS_LICENSE, MLX_LICENSE, MLX_C_LICENSE, CPP_HTTPLIB_LICENSE, DLPACK_LICENSE, FMT_LICENSE, PICOJSON_LICENSE, XGRAMMAR_LICENSE and XGRAMMAR_NOTICE. The private companion retains all of these plus the previously acquired Ollama MIT text and exact Qwen Apache-2.0 license layer.

The portable install-only Python archive supplies CPython LICENSE.txt but lacks the full build archive's dependency license inventory. Static native dependency notice completeness (including OpenSSL 3.5.9) remains unverified. Do not substitute notices from a different installed OpenSSL build or claim complete redistribution review. No new download was made for this notice review.
