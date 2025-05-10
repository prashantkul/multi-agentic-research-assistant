"""Document ingestion utility for preparing research papers."""
import os
import shutil
import requests
from typing import List, Optional, Union
from urllib.parse import urlparse
import glob

class DocumentIngestion:
    """Utility for ingesting research papers."""

    def __init__(self, papers_directory: str = "data/papers"):
        """Initialize document ingestion.

        Args:
            papers_directory: Directory to store papers
        """
        self.papers_directory = papers_directory
        os.makedirs(papers_directory, exist_ok=True)

    def download_paper(self, url: str, filename: Optional[str] = None) -> str:
        """Download a research paper from a URL.

        Args:
            url: URL to download from
            filename: Optional filename to save as

        Returns:
            Path to downloaded file
        """
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)

            # If no extension or empty filename, generate one
            if not filename or '.' not in filename:
                filename = f"paper_{len(os.listdir(self.papers_directory)) + 1}.pdf"

        save_path = os.path.join(self.papers_directory, filename)

        # Download file
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            print(f"Downloaded {url} to {save_path}")
            return save_path
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            raise

    def import_local_paper(self, file_path: str) -> str:
        """Import a local paper into the papers directory.

        Args:
            file_path: Path to local file

        Returns:
            Path to imported file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        save_path = os.path.join(self.papers_directory, filename)

        # Copy file
        shutil.copy2(file_path, save_path)
        print(f"Imported {file_path} to {save_path}")

        return save_path

    def import_from_directory(self, directory_path: str) -> List[str]:
        """Import all PDF and text files from a directory.

        Args:
            directory_path: Path to directory

        Returns:
            List of paths to imported files
        """
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")

        # Find all PDF and text files in the directory
        pdf_files = glob.glob(os.path.join(directory_path, "**/*.pdf"), recursive=True)
        txt_files = glob.glob(os.path.join(directory_path, "**/*.txt"), recursive=True)
        all_files = pdf_files + txt_files

        if not all_files:
            print(f"No PDF or text files found in {directory_path}")
            return []

        imported_paths = []
        for file_path in all_files:
            try:
                imported_path = self.import_local_paper(file_path)
                imported_paths.append(imported_path)
            except Exception as e:
                print(f"Error importing {file_path}: {e}")

        return imported_paths

    def batch_import_papers(self, sources: List[Union[str, dict]]) -> List[str]:
        """Import multiple papers from URLs, local paths, or directories.

        Args:
            sources: List of URLs, file paths, or directories

        Returns:
            List of paths to imported files
        """
        imported_paths = []

        for source in sources:
            try:
                if isinstance(source, dict) and 'url' in source:
                    # Dictionary with URL and optional filename
                    path = self.download_paper(source['url'], source.get('filename'))
                    imported_paths.append(path)
                elif isinstance(source, str):
                    if source.startswith(('http://', 'https://')):
                        # URL
                        path = self.download_paper(source)
                        imported_paths.append(path)
                    elif os.path.isdir(source):
                        # Directory
                        paths = self.import_from_directory(source)
                        imported_paths.extend(paths)
                    elif os.path.isfile(source):
                        # File
                        path = self.import_local_paper(source)
                        imported_paths.append(path)
                    else:
                        print(f"Invalid source: {source}")
            except Exception as e:
                print(f"Error importing {source}: {e}")

        return imported_paths