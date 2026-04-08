from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from downloader.datatourisme_download import DatatoursimeDownload

def test_deployment_smoke_extract_data_creates_files_and_clears_checkpoint(monkeypatch, tmp_path):
	downloader = DatatoursimeDownload(
		api_key="demo-key",
		url_api="https://example.org/api",
		path_output=str(tmp_path / "output"),
		path_state=str(tmp_path / "checkpoint.json"),
		page_file=2,
		page_size=2,
		time_sleep=0,
	)

	responses = [
		{
			"objects": [{"id": 1}, {"id": 2}],
			"meta": {"next": "https://example.org/api?page=2"},
		},
		{
			"objects": [{"id": 3}],
			"meta": {"next": None},
		},
	]

	def fake_fetch(url):
		return responses.pop(0)

	monkeypatch.setattr(downloader, "_fetch_with_retry", fake_fetch)
	monkeypatch.setattr("time.sleep", lambda *_: None)

	total = downloader.extract_data()

	first_file = Path(downloader._get_output_filename(1))
	assert total == 3
	assert first_file.exists()
	assert first_file.read_text(encoding="utf-8").count("\n") == 3
	assert not Path(downloader.path_state).exists()


def test_deployment_resume_from_checkpoint(monkeypatch, tmp_path):
	downloader = DatatoursimeDownload(
		api_key="demo-key",
		url_api="https://example.org/api",
		path_output=str(tmp_path / "output"),
		path_state=str(tmp_path / "checkpoint.json"),
		page_file=10,
		page_size=2,
		time_sleep=0,
	)

	downloader._ensure_output_dir()
	downloader._save_checkpoint(
		next_url="https://example.org/api?page=3",
		total_count=4,
		page_count=2,
		file_index=1,
	)

	seen_urls = []

	def fake_fetch(url):
		seen_urls.append(url)
		return {
			"objects": [{"id": 5}, {"id": 6}],
			"meta": {"next": None},
		}

	monkeypatch.setattr(downloader, "_fetch_with_retry", fake_fetch)
	monkeypatch.setattr("time.sleep", lambda *_: None)

	total = downloader.extract_data()

	assert seen_urls == ["https://example.org/api?page=3"]
	assert total == 6
