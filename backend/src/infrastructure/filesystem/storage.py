from __future__ import annotations

from pathlib import Path


class EncryptedBlobStorage:
	def __init__(self, root_path: str) -> None:
		self._root = Path(root_path).expanduser().resolve()
		self._root.mkdir(parents=True, exist_ok=True)

	def build_path(self, storage_name: str) -> Path:
		return self._root / storage_name

	def write(self, storage_name: str, content: bytes) -> str:
		path = self.build_path(storage_name)
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_bytes(content)
		return str(path)

	def read(self, storage_name: str) -> bytes:
		path = self.build_path(storage_name)
		return path.read_bytes()

	def delete(self, storage_name: str) -> None:
		path = self.build_path(storage_name)
		if not path.exists():
			raise FileNotFoundError(str(path))
		path.unlink()