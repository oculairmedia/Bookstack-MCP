import unittest

from fastmcp_server.bookstack.tools import _filter_collection


class FilterCollectionTests(unittest.TestCase):
    def test_filters_dict_payload(self) -> None:
        payload = {"data": [{"book_id": 1}, {"book_id": 2}], "count": 2}

        filtered, match_count = _filter_collection(payload, lambda item: item.get("book_id") == 1)

        self.assertEqual(filtered["data"], [{"book_id": 1}])
        self.assertEqual(filtered["count"], 1)
        self.assertEqual(match_count, 1)

    def test_filters_list_payload(self) -> None:
        payload = [
            {"chapter_id": 10},
            {"chapter_id": 11},
            {"chapter_id": 10},
        ]

        filtered, match_count = _filter_collection(payload, lambda item: item.get("chapter_id") == 10)

        self.assertEqual(filtered, [{"chapter_id": 10}, {"chapter_id": 10}])
        self.assertEqual(match_count, 2)

    def test_returns_original_when_no_predicate(self) -> None:
        payload = {"data": [{"book_id": 1}], "count": 1}

        filtered, match_count = _filter_collection(payload, None)

        self.assertIs(filtered, payload)
        self.assertIsNone(match_count)


if __name__ == "__main__":
    unittest.main()
