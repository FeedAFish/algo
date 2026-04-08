import json
from pathlib import Path
import pytest
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from downloader.datatourisme_download import DatatoursimeDownload

@pytest.fixture
def downloader(tmp_path):
	return DatatoursimeDownload(
		api_key="demo-key",
		url_api="https://example.org/api",
		path_output=str(tmp_path / "output"),
		path_state=str(tmp_path / "checkpoint.json"),
		page_file=2,
		page_size=100,
		time_sleep=0,
	)


def test_get_output_filename_formats_index(downloader):
	filename = downloader._get_output_filename(3)
	assert filename.endswith("data_part_0003.ndjson")


def test_ensure_output_dir_creates_directory(downloader):
	output_dir = Path(downloader.path_output)
	assert not output_dir.exists()

	downloader._ensure_output_dir()

	assert output_dir.exists()
	assert output_dir.is_dir()


def test_append_ndjson_writes_one_json_object_per_line(downloader):
	downloader._ensure_output_dir()
	target = downloader._get_output_filename(1)

	payload = [
		{"id": 1, "name": "A"},
		{"id": 2, "name": "B"},
	]

	downloader._append_ndjson(payload, target)

	lines = Path(target).read_text(encoding="utf-8").splitlines()
	assert len(lines) == 2
	assert json.loads(lines[0]) == {"id": 1, "name": "A"}
	assert json.loads(lines[1]) == {"id": 2, "name": "B"}


def test_save_and_load_checkpoint_roundtrip(downloader):
	downloader._save_checkpoint(
		next_url="https://example.org/api?page=2",
		total_count=200,
		page_count=2,
		file_index=1,
	)

	checkpoint = downloader._load_checkpoint()

	assert checkpoint == {
		"next_url": "https://example.org/api?page=2",
		"total_count": 200,
		"page_count": 2,
		"file_index": 1,
	}


def test_count_existing_objects_counts_all_ndjson_lines(downloader):
	downloader._ensure_output_dir()
	file1 = Path(downloader._get_output_filename(1))
	file2 = Path(downloader._get_output_filename(2))

	file1.write_text('{"id": 1}\n{"id": 2}\n', encoding="utf-8")
	file2.write_text('{"id": 3}\n', encoding="utf-8")

	assert downloader.count_existing_objects(downloader.path_output) == 3


def test_extract_types_returns_all_type_values(downloader):
	downloader._ensure_output_dir()
	file1 = Path(downloader._get_output_filename(1))
	file2 = Path(downloader._get_output_filename(2))

	file1.write_text(
		'{"type": ["Museum", "Place"]}\n'
		'{"type": ["Event"]}\n',
		encoding="utf-8",
	)
	file2.write_text(
		'{"type": ["Restaurant"]}\n'
		'{"type": []}\n',
		encoding="utf-8",
	)

	assert downloader.extract_types() == ["Museum", "Place", "Event", "Restaurant"]
