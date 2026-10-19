import unittest
from launch_deets.data import load_archive, split_documents


class ChunkingTests(unittest.TestCase):
    def test_archive_boundaries_and_provenance(self):
        for doc in load_archive().documents:
            chunks = split_documents([doc])
            previous = -1
            for chunk in chunks:
                text, meta = chunk['text'], chunk['metadata']
                start = meta['start_index']
                with self.subTest(document=meta['document_id'], start=start):
                    self.assertGreater(start, previous)
                    self.assertEqual(doc['text'][start:start + len(text)], text)
                    self.assertLessEqual(len(text), 500)
                    self.assertFalse(start > 0 and doc['text'][start-1].isalnum() and text[0].isalnum(), 'Chunk begins inside a word')
                    end = start + len(text)
                    self.assertFalse(end < len(doc['text']) and text[-1].isalnum() and doc['text'][end].isalnum(), 'Chunk ends inside a word')
                    for key, value in doc['metadata'].items():
                        self.assertEqual(meta[key], value)
                previous = start

    def test_word_level_overlap_and_coverage(self):
        text = ' '.join(f'word{i:03}' for i in range(80))
        chunks = split_documents([{'text': text, 'metadata': {'document_id': 'TEST'}}], 80, 24)
        self.assertEqual({w for c in chunks for w in c['text'].split()}, set(text.split()))
        for left, right in zip(chunks, chunks[1:]):
            self.assertLess(right['metadata']['start_index'], left['metadata']['start_index'] + len(left['text']))

    def test_empty_and_short_documents(self):
        self.assertEqual(split_documents([]), [])
        self.assertEqual(split_documents([{'text': '', 'metadata': {}}]), [])
        result = split_documents([{'text': '  short text  ', 'metadata': {'document_id': 'TEST'}}])
        self.assertEqual(result[0]['text'], 'short text')
        self.assertEqual(result[0]['metadata']['start_index'], 2)

    def test_invalid_settings(self):
        for size, overlap in [(0, 0), (10, -1), (10, 10)]:
            with self.assertRaises(ValueError):
                split_documents([], size, overlap)
