"""Windows handle-relative source access; never fall back to path-based reads.

Native validation is required before enabling the Windows editor release profile.
NtCreateFile opens each component relative to its retained parent handle, bypasses
reparse processing, and denies concurrent write/delete sharing.
"""

import ctypes
import os
import re
import struct
from contextlib import contextmanager
from pathlib import Path

from thread_agent.domain.records import AgentError


def components(name):
    parts = name.split("/")
    if not name or any(
        not part
        or part in {".", ".."}
        or re.search(r'[\\:\x00-\x1f<>"|?*]', part)
        or part.endswith((".", " "))
        or re.match(r"^(con|prn|aux|nul|clock\$|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)", part, re.I)
        for part in parts
    ):
        raise AgentError("Invalid Windows source path.")
    return parts


class API:
    def __init__(self):
        if os.name != "nt":
            raise AgentError("Windows handle access requires native Windows.")
        from ctypes import wintypes as w

        class UnicodeString(ctypes.Structure):
            _fields_ = [("Length", w.USHORT), ("MaximumLength", w.USHORT), ("Buffer", w.LPWSTR)]

        class Attributes(ctypes.Structure):
            _fields_ = [
                ("Length", w.ULONG),
                ("RootDirectory", w.HANDLE),
                ("ObjectName", ctypes.POINTER(UnicodeString)),
                ("Attributes", w.ULONG),
                ("SecurityDescriptor", w.LPVOID),
                ("SecurityQualityOfService", w.LPVOID),
            ]

        class Status(ctypes.Structure):
            _fields_ = [("Status", ctypes.c_void_p), ("Information", ctypes.c_size_t)]

        class Information(ctypes.Structure):
            _fields_ = [
                ("attributes", w.DWORD),
                ("created", w.FILETIME),
                ("accessed", w.FILETIME),
                ("written", w.FILETIME),
                ("volume", w.DWORD),
                ("sizeHigh", w.DWORD),
                ("sizeLow", w.DWORD),
                ("links", w.DWORD),
                ("indexHigh", w.DWORD),
                ("indexLow", w.DWORD),
            ]

        self.UnicodeString, self.Attributes, self.Status = UnicodeString, Attributes, Status
        self.Information = Information
        self.nt = ctypes.WinDLL("ntdll", use_last_error=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.nt.NtCreateFile.argtypes = [
            ctypes.POINTER(w.HANDLE),
            w.DWORD,
            ctypes.POINTER(Attributes),
            ctypes.POINTER(Status),
            w.LPVOID,
            w.ULONG,
            w.ULONG,
            w.ULONG,
            w.ULONG,
            w.LPVOID,
            w.ULONG,
        ]
        self.nt.NtCreateFile.restype = ctypes.c_long
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.GetFileInformationByHandle.argtypes = [w.HANDLE, ctypes.POINTER(Information)]
        self.kernel.GetFileType.argtypes = [w.HANDLE]
        self.kernel.GetDriveTypeW.argtypes = [w.LPCWSTR]
        self.kernel.ReadFile.argtypes = [
            w.HANDLE,
            w.LPVOID,
            w.DWORD,
            ctypes.POINTER(w.DWORD),
            w.LPVOID,
        ]
        self.kernel.GetFileInformationByHandleEx.argtypes = [
            w.HANDLE,
            ctypes.c_int,
            w.LPVOID,
            w.DWORD,
        ]

    def open(self, name, parent=None, directory=False):
        from ctypes import wintypes as w

        text = ctypes.create_unicode_buffer(name)
        length = len(name.encode("utf-16-le"))
        if length > 65532:
            raise AgentError("Windows source path exceeds native length limit.")
        string = self.UnicodeString(length, length + 2, ctypes.cast(text, w.LPWSTR))
        attributes = self.Attributes(
            ctypes.sizeof(self.Attributes), parent, ctypes.pointer(string), 0x40, None, None
        )
        status, handle = self.Status(), w.HANDLE()
        # FILE_OPEN, synchronous IO, open reparse point itself, directory/file requirement.
        result = self.nt.NtCreateFile(
            ctypes.byref(handle),
            0x120089,
            ctypes.byref(attributes),
            ctypes.byref(status),
            None,
            0,
            1,
            1,
            0x20 | 0x200000 | (1 if directory else 0x40),
            None,
            0,
        )
        if result < 0:
            raise AgentError(
                f"Cannot securely open Windows source (NTSTATUS {result & 0xFFFFFFFF:08x})."
            )
        try:
            info = self.info(handle)
            if info.attributes & 0x400 or bool(info.attributes & 0x10) != directory:
                raise AgentError("Windows source is a reparse point or has the wrong type.")
            return handle
        except Exception:
            self.kernel.CloseHandle(handle)
            raise

    def info(self, handle):
        info = self.Information()
        if not self.kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise AgentError("Cannot inspect Windows source handle.")
        if self.kernel.GetFileType(handle) != 1:
            raise AgentError("Windows source is not a disk file.")
        return info


@contextmanager
def handles(root, parts, directory=False):
    api, retained = API(), []
    try:
        absolute = str(Path(root).resolve(strict=True))
        if not re.match(r"^[A-Za-z]:\\", absolute):
            raise AgentError("Windows sources require a local drive, not a UNC/device namespace.")
        if api.kernel.GetDriveTypeW(absolute[:3]) not in {2, 3}:
            raise AgentError("Windows sources require a local fixed or removable drive.")
        retained.append(api.open("\\??\\" + absolute, directory=True))
        for index, part in enumerate(parts):
            retained.append(
                api.open(part, retained[-1], directory=index < len(parts) - 1 or directory)
            )
        yield api, retained[-1]
    finally:
        for handle in reversed(retained):
            api.kernel.CloseHandle(handle)


def read_bytes(root, name, limit):
    from ctypes import wintypes as w

    with handles(root, components(name)) as (api, handle):
        before = api.info(handle)
        size = before.sizeHigh << 32 | before.sizeLow
        if before.links != 1 or size > limit:
            raise AgentError("Windows source is hard-linked or exceeds the byte limit.")
        data = bytearray()
        while len(data) <= limit:
            buffer = ctypes.create_string_buffer(min(8192, limit + 1 - len(data)))
            received = w.DWORD()
            if not api.kernel.ReadFile(handle, buffer, len(buffer), ctypes.byref(received), None):
                raise AgentError("Cannot read Windows source handle.")
            if not received.value:
                break
            data.extend(buffer.raw[: received.value])
        after = api.info(handle)
        if (
            after.links != 1
            or len(data) > limit
            or size != (after.sizeHigh << 32 | after.sizeLow)
            or (before.written.dwLowDateTime, before.written.dwHighDateTime)
            != (after.written.dwLowDateTime, after.written.dwHighDateTime)
        ):
            raise AgentError("Windows source changed during reading.")
        return bytes(data)


def entries(root, directory):
    relative = Path(directory).relative_to(root).as_posix()
    parts = [] if relative == "." else components(relative)
    with handles(root, parts, directory=True) as (api, handle):
        result, first = [], True
        while True:
            buffer = ctypes.create_string_buffer(65536)
            # FILE_ID_BOTH_DIR_INFO: Restart class 11, subsequent class 10.
            if not api.kernel.GetFileInformationByHandleEx(
                handle, 11 if first else 10, buffer, len(buffer)
            ):
                if ctypes.get_last_error() == 18:
                    break
                raise AgentError("Cannot enumerate Windows source handle.")
            first, offset = False, 0
            while True:
                following = struct.unpack_from("<I", buffer, offset)[0]
                attributes, length = struct.unpack_from("<II", buffer, offset + 56)
                if length > 65536 - offset - 104 or length % 2:
                    raise AgentError("Invalid Windows directory enumeration.")
                name = buffer.raw[offset + 104 : offset + 104 + length].decode("utf-16-le")
                if name not in {".", ".."}:
                    result.append((name, bool(attributes & 0x10), bool(attributes & 0x400)))
                    if len(result) > 20000:
                        raise AgentError("A directory exceeds the 20,000-entry scan limit.")
                if not following:
                    break
                if following < 104 or offset + following >= 65536:
                    raise AgentError("Invalid Windows directory offset.")
                offset += following
        return sorted(result)
