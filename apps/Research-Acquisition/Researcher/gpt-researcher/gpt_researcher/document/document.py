import asyncio
import os
from typing import List, Union
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredCSVLoader,
UnstructuredEPubLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader
)
from langchain_community.document_loaders import BSHTMLLoader


class DocumentLoader:

    def __init__(self, path: Union[str, List[str]], receipt=None):
        self.path = path
        # Optional ReadReceipt (gpt_researcher.receipts): every file found is
        # recorded as loaded, or skipped with the reason.
        self.receipt = receipt
        # Files over this many bytes are skipped (0 = no cap).
        self.max_bytes = int(os.getenv("LOCAL_DOCUMENT_MAX_BYTES", "0") or 0)

    def _key(self, file_path: str) -> str:
        """The name a file goes by in the receipt: relative to the folder, like the docs' url."""
        if isinstance(self.path, (str, bytes, os.PathLike)):
            return os.path.relpath(file_path, self.path)
        return os.path.basename(file_path)

    def _queue(self, tasks: list, file_path: str, file_extension: str) -> None:
        """Record the file and queue it, unless the size cap rules it out."""
        try:
            size = os.path.getsize(file_path)
        except OSError:
            size = None
        if self.receipt:
            self.receipt.file_found(self._key(file_path), size)
        if self.max_bytes and size is not None and size > self.max_bytes:
            if self.receipt:
                self.receipt.file_skipped(self._key(file_path), f"size cap: {size} bytes > {self.max_bytes}")
            return
        tasks.append(self._load_document(file_path, file_extension))

    async def load(self) -> list:
        tasks = []
        if isinstance(self.path, list):
            for file_path in self.path:
                if os.path.isfile(file_path):  # Ensure it's a valid file
                    filename = os.path.basename(file_path)
                    file_name, file_extension_with_dot = os.path.splitext(filename)
                    file_extension = file_extension_with_dot.strip(".").lower()
                    self._queue(tasks, file_path, file_extension)

        elif isinstance(self.path, (str, bytes, os.PathLike)):
            for root, dirs, files in os.walk(self.path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_name, file_extension_with_dot = os.path.splitext(file)
                    file_extension = file_extension_with_dot.strip(".").lower()
                    self._queue(tasks, file_path, file_extension)

        else:
            raise ValueError("Invalid type for path. Expected str, bytes, os.PathLike, or list thereof.")

        # for root, dirs, files in os.walk(self.path):
        #     for file in files:
        #         file_path = os.path.join(root, file)
        #         file_name, file_extension_with_dot = os.path.splitext(file_path)
        #         file_extension = file_extension_with_dot.strip(".")
        #         tasks.append(self._load_document(file_path, file_extension))

        # Large recursive corpora used to start every parser at once, which can
        # exhaust memory/file handles.  Process a configurable batch at a time.
        batch_size = max(1, int(os.getenv("LOCAL_DOCUMENT_BATCH_SIZE", "24")))
        docs = []
        for offset in range(0, len(tasks), batch_size):
            for pages in await asyncio.gather(*tasks[offset:offset + batch_size]):
                for page in pages:
                    if page.page_content:
                        docs.append({
                            "raw_content": page.page_content,
                            "url": os.path.relpath(page.metadata['source'], self.path)
                            if isinstance(self.path, (str, bytes, os.PathLike))
                            else os.path.basename(page.metadata['source'])
                        })
                    
        if not docs:
            raise ValueError("🤷 Failed to load any documents!")

        return docs

    async def _load_document(self, file_path: str, file_extension: str) -> list:
        ret_data = []
        reason = None
        try:
            loader_dict = {
                "pdf": PyMuPDFLoader(file_path),
"epub": UnstructuredEPubLoader(file_path),
                "txt": TextLoader(file_path),
                "doc": UnstructuredWordDocumentLoader(file_path),
                "docx": UnstructuredWordDocumentLoader(file_path),
                "pptx": UnstructuredPowerPointLoader(file_path),
                "csv": UnstructuredCSVLoader(file_path, mode="elements"),
                "xls": UnstructuredExcelLoader(file_path, mode="elements"),
                "xlsx": UnstructuredExcelLoader(file_path, mode="elements"),
                "md": UnstructuredMarkdownLoader(file_path),
                "html": BSHTMLLoader(file_path),
                "htm": BSHTMLLoader(file_path)
            }

            loader = loader_dict.get(file_extension, None)
            if loader:
                try:
                    ret_data = loader.load()
                except Exception as e:
                    print(
                        f"Failed to load {file_extension or 'unknown'} document: {file_path}"
                    )
                    print(e)
                    reason = f"error: {type(e).__name__}: {str(e)[:200]}"
            else:
                reason = f"unsupported type: .{file_extension}" if file_extension else "unsupported type: no extension"

        except Exception as e:
            print(f"Failed to load document : {file_path}")
            print(e)
            reason = f"error: {type(e).__name__}: {str(e)[:200]}"

        if self.receipt:
            text = [p for p in ret_data if p.page_content]
            if reason:
                self.receipt.file_skipped(self._key(file_path), reason)
            elif not text:
                self.receipt.file_skipped(self._key(file_path), "empty: no text extracted")
            else:
                self.receipt.file_loaded(self._key(file_path), len(text), sum(len(p.page_content) for p in text))

        return ret_data
